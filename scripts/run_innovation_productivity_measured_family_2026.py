#!/usr/bin/env python3
"""Frozen two-test innovation/productivity descriptive family.

Source and key checks do not open measured columns. The value path requires a
first-addition registration commit followed by a separate source-lock commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_innovation_productivity_measured_family_2026.py"
PLAN = "engine/audits/innovation_productivity_measured_family_prereg_2026-10-09.md"
LOCK = "data/pinned_evidence/innovation_productivity_measured_family_2026.manifest.json"
FAMILY = "innovation_productivity_measured_family_2026_10_09"
FAMILY_P_MAX = 0.025  # two-sided Bonferroni 0.05 / two fixed tests
START_YEAR, END_YEAR = 1995, 2021
MIN_PAIRS, MIN_COUNTRIES, MIN_YEARS, MIN_VARYING = 400, 20, 5, 15
COUNTRIES = frozenset((
    "AUS AUT BEL BGR CAN CHE CHL COL CRI CZE DEU DNK ESP EST FIN FRA GBR GRC "
    "HRV HUN IRL ISL ISR ITA LTU LUX LVA MEX NLD NOR NZL POL PRT ROU SVK "
    "SVN SWE USA"
).split())
if len(COUNTRIES) != 38:
    raise RuntimeError("frozen 38-country source-key roster changed")

SOURCES = {
    "pdb": {
        "source": "oecd:DSD_PDB",
        "path": "data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet",
        "sha256": "3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c",
        "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
        "series_id": "DSD_PDB",
    },
    "patents": {
        "source": "wipo:patent_applications_resident",
        "path": "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
        "sha256": "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
        "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
        "series_id": "patent_applications_resident",
    },
    "population": {
        "source": "world_bank_wdi:SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "SP.POP.TOTL",
    },
    "hightech": {
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "path": "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet",
        "sha256": "b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "TX.VAL.TECH.MF.ZS",
    },
}
TESTS = {
    "resident_patents_manufacturing_productivity_forward_2026": {
        "topic": "growth",
        "treatment": "patents",
        "outcome": "pdb",
        "measurement_limit": "Patent filing intensity is not invention quality; manufacturing productivity growth can reflect demand, hours, and revisions.",
    },
    "manufacturing_productivity_hightech_export_mix_forward_2026": {
        "topic": "trade",
        "treatment": "pdb",
        "outcome": "hightech",
        "measurement_limit": "High-tech exports are a share of manufactured export value, not total exports, product complexity, or domestic value added.",
    },
}
PDB_KEYS = ["REF_AREA", "FREQ", "MEASURE", "ACTIVITY", "UNIT_MEASURE", "PRICE_BASE", "TRANSFORMATION", "ASSET_CODE", "CONVERSION_TYPE", "period"]
PDB_FILTER = {
    "FREQ": "A", "MEASURE": "GVAHRS", "ACTIVITY": "C", "UNIT_MEASURE": "XDC_H",
    "PRICE_BASE": "LR", "TRANSFORMATION": "GY", "ASSET_CODE": "_Z", "CONVERSION_TYPE": "_Z",
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit for {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from {revision}: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = TESTS[hypothesis_id]["topic"]
    return (f"hypotheses/{topic}/{hypothesis_id}.yaml",
            f"hypotheses/steelman/{hypothesis_id}.md", f"engine/runs/{hypothesis_id}")


def registration_commit() -> str:
    files = [RUNNER, PLAN]
    for hypothesis_id in TESTS:
        spec, steelman, _ = paths(hypothesis_id)
        files.extend([spec, steelman])
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("family lacks one shared first-addition registration commit")
    revision = revisions.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    for hypothesis_id in TESTS:
        if git("ls-tree", "-r", "--name-only", revision, "--", paths(hypothesis_id)[2]).strip():
            raise RuntimeError("registration commit contained result artifacts")
    return revision


def validate_specs() -> None:
    for hypothesis_id, config in TESTS.items():
        spec_rel, steelman_rel, _ = paths(hypothesis_id)
        spec = yaml.safe_load((ROOT / spec_rel).read_text())
        threshold = spec["falsification"]["threshold"]
        expected = {
            "family_id": FAMILY, "family_size": 2, "family_alpha": 0.05,
            "family_p_max": FAMILY_P_MAX, "expected_sign": "+",
            "min_observations": MIN_PAIRS, "min_countries": MIN_COUNTRIES,
            "min_pairs_per_country": MIN_YEARS, "min_varying_countries": MIN_VARYING,
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_credit": 0,
        }
        if any(threshold.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"frozen threshold mismatch: {hypothesis_id}")
        if threshold.get("source_files") != SOURCES:
            raise RuntimeError(f"source pins differ from runner: {hypothesis_id}")
        if (spec.get("hypothesis_id") != hypothesis_id or spec.get("status") != "pre_registered"
                or spec.get("claim_direction") != "+" or spec.get("evidence_type") != "associational"
                or spec["sample"].get("countries") != sorted(COUNTRIES)
                or spec["sample"].get("period") != [START_YEAR, END_YEAR]
                or spec.get("steelman") != steelman_rel or spec.get("covers_claims") != []
                or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []):
            raise RuntimeError(f"registration content mismatch: {hypothesis_id}")
        if (spec["variables"]["treatment"][0]["source"] != SOURCES[config["treatment"]]["source"]
                or spec["variables"]["outcome"][0]["source"] != SOURCES[config["outcome"]]["source"]):
            raise RuntimeError(f"registered source pair mismatch: {hypothesis_id}")


def check_sources() -> None:
    for role, source in SOURCES.items():
        path = ROOT / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched source: {role}")
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        entries = [item for item in manifest["entries"]
                   if item.get("parquet_path") == source["path"] and item.get("series_id") == source["series_id"]]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"tracked fetch manifest does not custody {role}")


def lock_payload(revision: str) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision, "sources": SOURCES,
            "note": "Exact fetched vintages locked after registration and before opening measured columns."}


def write_lock() -> None:
    revision = registration_commit()
    validate_specs()
    check_sources()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lock_payload(revision), indent=2, sort_keys=True) + "\n")


def check_lock(revision: str) -> None:
    target = ROOT / LOCK
    if json.loads(target.read_text()) != lock_payload(revision):
        raise RuntimeError("source lock differs from frozen pins")
    lock_revision = first_addition(LOCK)
    if lock_revision == revision:
        raise RuntimeError("source lock was not a separate later commit")
    committed_unchanged(LOCK, lock_revision)
    for hypothesis_id in TESTS:
        if git("ls-tree", "-r", "--name-only", lock_revision, "--", paths(hypothesis_id)[2]).strip():
            raise RuntimeError("source-lock commit contained results")


def pdb_frame(with_values: bool) -> pd.DataFrame:
    columns = PDB_KEYS + (["value"] if with_values else [])
    frame = pd.read_parquet(ROOT / SOURCES["pdb"]["path"], columns=columns)
    for key, value in PDB_FILTER.items():
        frame = frame.loc[frame[key].eq(value)]
    frame = frame.rename(columns={"REF_AREA": "country_iso3", "period": "year"})
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES), ["country_iso3", "year"] + (["value"] if with_values else [])].copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate exact PDB country-year-measure keys")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def annual_frame(role: str, with_values: bool) -> pd.DataFrame:
    frame = pd.read_parquet(ROOT / SOURCES[role]["path"],
                            columns=["country_iso3", "year"] + (["value"] if with_values else []))
    frame = frame.loc[frame.country_iso3.isin(COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate source keys: {role}")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def build_panel(hypothesis_id: str, with_values: bool) -> pd.DataFrame:
    base = pdb_frame(with_values).rename(columns={"value": "baseline_productivity"})
    base = base.loc[base.year.between(START_YEAR, END_YEAR)].copy()
    if hypothesis_id == "resident_patents_manufacturing_productivity_forward_2026":
        patents = annual_frame("patents", with_values).rename(columns={"value": "patents"})
        population = annual_frame("population", with_values).rename(columns={"value": "population"})
        panel = base.merge(patents, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel.merge(population, on=["country_iso3", "year"], validate="one_to_one")
        for offset in (1, 2, 3):
            future = pdb_frame(with_values).rename(columns={"value": f"productivity_{offset}"})
            future["year"] -= offset
            panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    else:
        hightech = annual_frame("hightech", with_values).rename(columns={"value": "baseline_hightech"})
        future = annual_frame("hightech", with_values).rename(columns={"value": "future_hightech"})
        future["year"] -= 3
        panel = base.merge(hightech, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    if not with_values:
        return panel
    value_cols = [name for name in panel.columns if name not in {"country_iso3", "year"}]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=value_cols).copy()
    if hypothesis_id == "resident_patents_manufacturing_productivity_forward_2026":
        panel = panel.loc[(panel.patents >= 0) & (panel.population > 0)].copy()
        panel["treatment"] = np.log1p(1_000_000 * panel.patents / panel.population)
        panel["outcome"] = panel[["productivity_1", "productivity_2", "productivity_3"]].mean(axis=1)
        panel["baseline"] = panel.baseline_productivity
    else:
        panel = panel.loc[panel.baseline_hightech.between(0, 100) & panel.future_hightech.between(0, 100)].copy()
        panel["treatment"] = panel.baseline_productivity
        panel["outcome"] = panel.future_hightech - panel.baseline_hightech
        panel["baseline"] = panel.baseline_hightech
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=["treatment", "outcome", "baseline"])
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def key_preflight() -> dict[str, dict[str, Any]]:
    output = {}
    for hypothesis_id in TESTS:
        panel = build_panel(hypothesis_id, False)
        counts = panel.groupby("country_iso3").size()
        eligible = counts[counts >= MIN_YEARS]
        output[hypothesis_id] = {
            "upper_pairs": int(eligible.sum()), "upper_countries": int(len(eligible)),
            "values_read": False, "null_masks_checked": False,
            "key_envelope_passed": bool(eligible.sum() >= MIN_PAIRS and len(eligible) >= MIN_COUNTRIES),
        }
    return output


def estimate_one(hypothesis_id: str) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    panel = build_panel(hypothesis_id, True)
    varying = int((panel.groupby("country_iso3").treatment.agg(lambda x: x.max() - x.min()) > 1e-10).sum()) if len(panel) else 0
    gate = {
        "observations": int(len(panel)), "countries": int(panel.country_iso3.nunique()),
        "varying_countries": varying, "min_pairs_per_country": MIN_YEARS,
        "treatment_years": [int(panel.year.min()), int(panel.year.max())] if len(panel) else [],
        "passed": bool(len(panel) >= MIN_PAIRS and panel.country_iso3.nunique() >= MIN_COUNTRIES and varying >= MIN_VARYING),
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case or treatment-variation floor failed", None
    fit = smf.ols("outcome ~ treatment + baseline + C(country_iso3) + C(year)", data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel.country_iso3, "use_correction": True}, use_t=False)
    if fit.model.rank != fit.model.exog.shape[1]:
        return gate, "INCONCLUSIVE", "registered fixed-effect design is rank deficient", None
    coefficient = float(fit.params["treatment"])
    se = float(fit.bse["treatment"])
    p = float(fit.pvalues["treatment"])
    ci = [float(x) for x in fit.conf_int().loc["treatment"]]
    r2 = float(fit.rsquared)
    if not all(math.isfinite(x) for x in (coefficient, se, p, r2, *ci)) or se <= 0 or not 0 <= p <= 1:
        return gate, "INCONCLUSIVE", "nonfinite or unidentified clustered estimate", None
    estimate = {"coefficient": coefficient, "std_error": se, "p_value": p, "ci95": ci,
                "n_obs": gate["observations"], "n_countries": gate["countries"], "r_squared": r2,
                "method": "country/year fixed-effect OLS; country-clustered normal-Wald standard errors"}
    if p <= FAMILY_P_MAX and coefficient > 0:
        return gate, "SUPPORTED", "positive coefficient clears frozen two-test family threshold", estimate
    if p <= FAMILY_P_MAX and coefficient < 0:
        return gate, "REFUTED", "negative coefficient clears frozen two-test family threshold", estimate
    return gate, "PARTIAL", "estimable association does not clear frozen directional family rule", estimate


def artifacts(hypothesis_id: str, revision: str, gate: dict[str, Any], verdict: str,
              reason: str, estimate: dict[str, Any] | None, stamp: str) -> dict[str, Any]:
    config = TESTS[hypothesis_id]
    spec_rel, steelman_rel, run_rel = paths(hypothesis_id)
    inputs = [{"role": role, **source} for role, source in SOURCES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "policy_score_credit": 0, "featured_eligible": False}
    limits = [
        "Descriptive country-panel association only; no causal or policy effect identified.",
        "Both tests share the OECD PDB manufacturing-productivity measure and many countries; they are not independent replications.",
        "Earlier patent/export and productivity evidence was visible before this registration; neither old verdict is inherited.",
        "WIPO patent data use World Bank API transport; outcome and treatment vintages are fixed by SHA-256.",
        config["measurement_limit"],
        "No school, position, policy, or featured score credit.",
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "estimate": estimate,
        "family_id": FAMILY, "family_size": 2, "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock": LOCK,
        "status": verdict, "vintages": inputs, "derived_panel": gate, "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_rel, "topic": config["topic"]},
        "preregistration": {"spec_commit": revision, "steelman": steelman_rel,
                            "family_id": FAMILY, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER, "run_dir": run_rel,
                         "command": f"python3 {RUNNER} --verify {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "n_observations": gate["observations"],
                 "n_countries": gate["countries"]},
        "results": estimate, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {revision}; source lock: {LOCK}.\n"
            f"Complete sample: {gate['observations']} country-year pairs, {gate['countries']} countries.\n"
            f"Family threshold: two-sided p <= {FAMILY_P_MAX:.6f} across two tests.\n")
    if estimate:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; clustered SE "
                 f"{estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += "\nMeasurement boundary: " + config["measurement_limit"] + "\nDescriptive calibration only; zero causal, school, policy, position, or featured credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               "raise SystemExit(subprocess.call([sys.executable, "
               f"str(root / {RUNNER!r}), '--verify', {hypothesis_id!r}], cwd=root))\n")
    chart = {"hypothesis_id": hypothesis_id, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None, "family_p_max": FAMILY_P_MAX}
    rows = [{"term": "treatment", **estimate}] if estimate else []
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart, "rows": rows}


def write_artifacts(hypothesis_id: str, payload: dict[str, Any]) -> None:
    spec_rel, _, run_rel = paths(hypothesis_id)
    folder = ROOT / run_rel
    if folder.exists():
        raise FileExistsError(run_rel)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["rows"], columns=["term", "coefficient", "std_error", "p_value",
                                                "ci95", "n_obs", "n_countries", "r_squared", "method"]).to_parquet(
                                                    folder / "coefficients.parquet", index=False)


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: mismatch")


def verify(hypothesis_id: str, revision: str) -> None:
    spec_rel, _, run_rel = paths(hypothesis_id)
    folder = ROOT / run_rel
    saved = json.loads((folder / "diagnostics.json").read_text())
    gate, verdict, reason, estimate = estimate_one(hypothesis_id)
    expected = artifacts(hypothesis_id, revision, gate, verdict, reason, estimate, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"), expected["rows"], "coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError("stored text differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check-sources", action="store_true")
    actions.add_argument("--write-source-lock", action="store_true")
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--verify", nargs="?", const="all", choices=[*TESTS, "all"])
    args = parser.parse_args()
    if args.check_sources:
        check_sources()
        print("four vintages match tracked fetch manifests; measured columns unopened")
        return 0
    if args.write_source_lock:
        write_lock()
        print(f"wrote {LOCK}; commit separately before measured-value access")
        return 0
    revision = registration_commit()
    validate_specs()
    check_sources()
    check_lock(revision)
    if args.preflight:
        report = key_preflight()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if all(item["key_envelope_passed"] for item in report.values()) else 1
    if args.run:
        if any((ROOT / paths(hypothesis_id)[2]).exists() for hypothesis_id in TESTS):
            raise FileExistsError("a family result already exists")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        payloads = {}
        for hypothesis_id in TESTS:
            gate, verdict, reason, estimate = estimate_one(hypothesis_id)
            payloads[hypothesis_id] = artifacts(hypothesis_id, revision, gate, verdict, reason, estimate, stamp)
        for hypothesis_id, payload in payloads.items():
            write_artifacts(hypothesis_id, payload)
            print(hypothesis_id, payload["diagnostics"]["verdict_label"], payload["diagnostics"]["preflight"])
        return 0
    for hypothesis_id in (TESTS if args.verify == "all" else [args.verify]):
        verify(hypothesis_id, revision)
        print("verified exact replay", hypothesis_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
