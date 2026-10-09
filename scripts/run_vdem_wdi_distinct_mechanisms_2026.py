#!/usr/bin/env python3
"""Run the frozen two-test V-Dem/WDI descriptive country holdout family.

The source-check command hashes files without opening measured columns. The
run command must only be used after the specs and source lock have separate
commits. It retains estimable null and contrary results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml


ROOT = Path(__file__).resolve().parents[1]
FAMILY_ID = "vdem_wdi_distinct_mechanisms_2026_10_09"
LOCK = ROOT / "data/pinned_evidence/vdem_wdi_distinct_mechanisms_2026.manifest.json"
P_MAX = 0.025  # two-sided Bonferroni: 0.05 / two registered tests
MIN_COUNTRIES = 35
MIN_DISTINCT_EXPOSURE_MEANS = 5
BASELINE_YEARS = range(2000, 2005)
END_YEARS = range(2019, 2024)

SOURCES = {
    "vdem": {
        "path": "data/vintages/vdem/vdem_cy_full@2026-05-05T200021Z.parquet",
        "sha256": "89afa79fba1ec71f06e60cc01d66d186b028636af63506f6bf7a1de36a7370ff",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source": "vdem:vdem_cy_full",
    },
    "codebook": {
        "path": "data/vintages/vdem/codebook@2026-05-05T200035Z.parquet",
        "sha256": "35fe28c5adc536016b1cfe3f615360d2906110cadecfd89818c1e2b92669a8b9",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source": "vdem:codebook",
    },
    "female_lfp": {
        "path": "data/vintages/world_bank_wdi/SL.TLF.CACT.FE.ZS@2026-05-05T194807Z.parquet",
        "sha256": "c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source": "world_bank_wdi:SL.TLF.CACT.FE.ZS",
    },
    "under5_mortality": {
        "path": "data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet",
        "sha256": "ad63729ccd5d1d4be6f3da5bbcac45b8a2c87d48c063cefeba8f0ddbe4b88f55",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source": "world_bank_wdi:SH.DYN.MORT",
    },
    "income": {
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
    },
}

TESTS = {
    "vdem_women_mobility_female_lfp_unseen_countries": {
        "spec": "hypotheses/labour/vdem_women_mobility_female_lfp_unseen_countries.yaml",
        "treatment_column": "v2cldmovew",
        "outcome_source": "female_lfp",
        "expected_sign": "+",
        "log_outcome": False,
    },
    "vdem_public_goods_child_mortality_unseen_countries": {
        "spec": "hypotheses/healthcare/vdem_public_goods_child_mortality_unseen_countries.yaml",
        "treatment_column": "v2dlencmps",
        "outcome_source": "under5_mortality",
        "expected_sign": "-",
        "log_outcome": True,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_sources(require_lock: bool = True) -> None:
    if require_lock:
        lock = json.loads(LOCK.read_text())
        if lock.get("family_id") != FAMILY_ID or lock.get("sources") != SOURCES:
            raise RuntimeError("source-lock manifest does not match frozen source pins")
        if subprocess.check_output(["git", "status", "--porcelain", "--", str(LOCK.relative_to(ROOT))], cwd=ROOT).strip():
            raise RuntimeError("source-lock manifest has uncommitted changes")
    for role, source in SOURCES.items():
        path = ROOT / source["path"]
        if not path.is_file():
            raise FileNotFoundError(f"missing pinned {role}: {path}")
        actual = sha256_file(path)
        if actual != source["sha256"]:
            raise RuntimeError(f"SHA-256 mismatch for {role}: {actual}")


def first_spec_commit(spec_path: str) -> str:
    commits = subprocess.check_output(
        ["git", "log", "--diff-filter=A", "--format=%H", "HEAD", "--", spec_path],
        cwd=ROOT,
        text=True,
    ).splitlines()
    if not commits:
        raise RuntimeError(f"spec has no committed registration: {spec_path}")
    return commits[-1]


def load_source_frames() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    vdem = pd.read_parquet(
        ROOT / SOURCES["vdem"]["path"],
        columns=["country_text_id", "year", "v2cldmovew", "v2dlencmps"],
    ).rename(columns={"country_text_id": "country_iso3"})
    vdem["year"] = vdem["year"].astype(int)
    frames = {}
    for role in ("female_lfp", "under5_mortality", "income"):
        frame = pd.read_parquet(ROOT / SOURCES[role]["path"], columns=["country_iso3", "year", "value"])
        frame["year"] = frame["year"].astype(int)
        frames[role] = frame
    return vdem, frames


def window_mean(frame: pd.DataFrame, country: str, years: range, column: str) -> float | None:
    values = pd.to_numeric(
        frame.loc[(frame["country_iso3"] == country) & frame["year"].isin(years), column],
        errors="coerce",
    ).to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    return float(values.mean()) if len(values) >= 3 else None


def make_country_rows(
    slug: str, vdem: pd.DataFrame, frames: dict[str, pd.DataFrame]
) -> tuple[list[dict], dict]:
    test = TESTS[slug]
    spec = yaml.safe_load((ROOT / test["spec"]).read_text())
    countries = spec["sample"]["countries"]
    rows: list[dict] = []
    for country in countries:
        exposure = window_mean(vdem, country, BASELINE_YEARS, test["treatment_column"])
        baseline = window_mean(frames[test["outcome_source"]], country, BASELINE_YEARS, "value")
        late = window_mean(frames[test["outcome_source"]], country, END_YEARS, "value")
        income = window_mean(frames["income"], country, BASELINE_YEARS, "value")
        if None in (exposure, baseline, late, income) or income <= 0:
            continue
        if test["log_outcome"] and (baseline <= 0 or late <= 0):
            continue
        baseline_control = math.log(baseline) if test["log_outcome"] else baseline
        change = (math.log(late) - math.log(baseline)) if test["log_outcome"] else (late - baseline)
        rows.append({
            "country_iso3": country,
            "treatment_mean": exposure,
            "baseline_outcome": baseline_control,
            "log_baseline_income": math.log(income),
            "outcome_change": change,
        })
    return rows, spec


def compute_result(slug: str, vdem: pd.DataFrame, frames: dict[str, pd.DataFrame]) -> dict:
    rows, spec = make_country_rows(slug, vdem, frames)
    n = len(rows)
    distinct = len({round(r["treatment_mean"], 10) for r in rows})
    result: dict = {
        "hypothesis_id": slug,
        "family_id": FAMILY_ID,
        "expected_sign": TESTS[slug]["expected_sign"],
        "p_max_two_sided": P_MAX,
        "n_countries": n,
        "distinct_exposure_means": distinct,
        "complete_country_iso3": [r["country_iso3"] for r in rows],
        "spec_commit": first_spec_commit(TESTS[slug]["spec"]),
        "sources": {k: dict(v) for k, v in SOURCES.items()},
        "data_gate_passed": n >= MIN_COUNTRIES and distinct >= MIN_DISTINCT_EXPOSURE_MEANS,
        "status": "INCONCLUSIVE",
        "reason": "insufficient complete countries or exposure variation",
    }
    if not result["data_gate_passed"]:
        return result
    x = np.array([r["treatment_mean"] for r in rows], dtype=float)
    x_sd = float(np.std(x, ddof=1))
    if not math.isfinite(x_sd) or x_sd <= 0:
        result["reason"] = "zero or invalid exposure standard deviation"
        return result
    x = (x - float(np.mean(x))) / x_sd
    design = np.column_stack([
        np.ones(n),
        x,
        np.array([r["baseline_outcome"] for r in rows], dtype=float),
        np.array([r["log_baseline_income"] for r in rows], dtype=float),
    ])
    outcome = np.array([r["outcome_change"] for r in rows], dtype=float)
    if np.linalg.matrix_rank(design) < design.shape[1]:
        result["reason"] = "singular registered design"
        return result
    fit = sm.OLS(outcome, design).fit(cov_type="HC3")
    beta = float(fit.params[1])
    p_value = float(fit.pvalues[1])
    se = float(fit.bse[1])
    if not all(map(math.isfinite, (beta, p_value, se))):
        result["reason"] = "non-finite registered estimate"
        return result
    expected = 1 if TESTS[slug]["expected_sign"] == "+" else -1
    status = "PARTIAL"
    if p_value <= P_MAX:
        status = "SUPPORTED" if beta * expected > 0 else "REFUTED"
    result.update({
        "status": status,
        "reason": "registered two-sided HC3 family rule",
        "coefficient_per_one_sample_sd": beta,
        "std_error_hc3": se,
        "p_value_two_sided_hc3": p_value,
        "ci95": [float(v) for v in fit.conf_int(alpha=0.05)[1]],
        "r_squared": float(fit.rsquared),
        "exposure_mean": float(np.mean([r["treatment_mean"] for r in rows])),
        "exposure_sd": x_sd,
        "baseline_years": [2000, 2004],
        "endpoint_years": [2019, 2023],
        "outcome_transform": "log_endpoint_minus_log_baseline" if TESTS[slug]["log_outcome"] else "endpoint_minus_baseline_percentage_points",
    })
    return result


def artifacts(slug: str, result: dict, run_utc: str) -> dict[str, str]:
    test = TESTS[slug]
    inputs = [
        {"role": role, "source": SOURCES[role]["source"], "vintage_file": SOURCES[role]["path"], "sha256": SOURCES[role]["sha256"], "source_manifest": SOURCES[role]["manifest"]}
        for role in ("vdem", test["outcome_source"], "income", "codebook")
    ]
    packet = {
        "packet_version": 1,
        "generated_utc": run_utc,
        "hypothesis": {"id": slug, "path": test["spec"], "topic": yaml.safe_load((ROOT / test["spec"]).read_text())["topic"]},
        "preregistration": {"spec_commit": result["spec_commit"], "family_id": FAMILY_ID, "family_p_max_two_sided": P_MAX, "family_size": 2},
        "reproduction": {"runner": "scripts/run_vdem_wdi_distinct_mechanisms_2026.py", "run_dir": f"engine/runs/{slug}", "command": "python3 scripts/run_vdem_wdi_distinct_mechanisms_2026.py --verify"},
        "verdict": {"raw": result["status"], "bucket": result["status"].lower(), "reason": result["reason"]},
        "data": {"inputs": inputs, "country_sample": result["complete_country_iso3"], "n_countries": result["n_countries"]},
        "results": {k: result[k] for k in ("coefficient_per_one_sample_sd", "std_error_hc3", "p_value_two_sided_hc3", "ci95", "r_squared") if k in result},
        "limitations": [
            "Descriptive country-level association, not a causal policy effect.",
            "The 61-country frame excludes old verified V-Dem-source samples but may overlap other IESET evidence.",
            "Early institutional measures and later outcomes may share unmeasured determinants.",
            "WDI and V-Dem source vintages are pinned by SHA-256; V-Dem's academic license requires citation.",
            "No school claim or position receives score credit.",
        ],
        "correction": {"disposition": "descriptive_calibration_only", "school_score_eligible": False, "school_score_credit": 0},
    }
    manifest = {
        "hypothesis_id": slug,
        "run_utc": run_utc,
        "runner": "scripts/run_vdem_wdi_distinct_mechanisms_2026.py",
        "preregistration_commit": result["spec_commit"],
        "source_lock": str(LOCK.relative_to(ROOT)),
        "status": result["status"],
        "vintages": inputs,
        "derived_panel": {"observations": result["n_countries"], "countries": result["n_countries"], "passed": result["data_gate_passed"]},
        "correction": {"disposition": "descriptive_calibration_only", "school_score_eligible": False, "school_score_credit": 0},
    }
    report = (
        f"# {slug}\n\n"
        f"- Verdict: **{result['status']}** — {result['reason']}\n"
        f"- Complete countries: {result['n_countries']} of 61 registered countries\n"
        f"- Family threshold: two-sided HC3 p ≤ {P_MAX}; two registered tests\n"
        f"- Descriptive calibration only; no causal or school-score credit.\n"
    )
    if "coefficient_per_one_sample_sd" in result:
        report += f"- Coefficient per one sample SD of exposure: {result['coefficient_per_one_sample_sd']:.6g}; two-sided p = {result['p_value_two_sided_hc3']:.6g}\n"
    return {
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True),
        "results.json": json.dumps(result, indent=2, sort_keys=True) + "\n",
        "replication_report.md": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check-sources", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    check_sources(require_lock=not args.check_sources)
    if args.check_sources:
        print("Pinned V-Dem/WDI raw sources match the frozen SHA-256 manifest entries.")
        return
    vdem, frames = load_source_frames()
    results = {slug: compute_result(slug, vdem, frames) for slug in TESTS}
    if args.verify:
        for slug, result in results.items():
            path = ROOT / "engine/runs" / slug / "results.json"
            observed = json.loads(path.read_text())
            if observed != result:
                raise RuntimeError(f"registered result replay differs: {slug}")
        print("Exact V-Dem/WDI registered result replay verified for both tests.")
        return
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for slug, result in results.items():
        out = ROOT / "engine/runs" / slug
        if out.exists():
            raise RuntimeError(f"result directory already exists: {out}")
        out.mkdir(parents=True)
        for name, content in artifacts(slug, result, run_utc).items():
            (out / name).write_text(content)
        print(slug, result["status"], "countries", result["n_countries"])


if __name__ == "__main__":
    main()
