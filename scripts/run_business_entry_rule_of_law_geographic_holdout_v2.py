#!/usr/bin/env python3
"""Run the preregistered, country-disjoint business-entry holdout.

Use --preflight to check only source hashes and coverage. --run refuses to
estimate until the new spec and steelman match committed HEAD content.
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
HYPOTHESIS_ID = "wdi_business_entry_rule_of_law_geographic_holdout_v2"
SPEC_REL = f"hypotheses/institutional_quality/{HYPOTHESIS_ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HYPOTHESIS_ID}.md"
RUN_REL = f"engine/runs/{HYPOTHESIS_ID}"
RUN_DIR = ROOT / RUN_REL
RUNNER_REL = "scripts/run_business_entry_rule_of_law_geographic_holdout_v2.py"

# This list is frozen from the old 60-country spec, not selected by the new data.
ORIGINAL_COUNTRIES = frozenset(
    "ALB ARG AUS AUT BEL BGD BRA CAN CHE CHL CHN COL CZE DEU DNK EGY ESP EST "
    "ETH FIN FRA GBR GHA GRC HUN IDN IND IRL ISR ITA JPN KAZ KEN KOR LTU "
    "LVA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL PRT ROU RUS SGP SVK "
    "SVN SWE THA TUR UKR USA VNM ZAF".split()
)

SOURCES = {
    "business_registrations": {
        "publisher": "world_bank_wdi",
        "series_id": "IC.BUS.NREG",
        "path": "data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet",
        "sha256": "213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/IC.BUS.NREG?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/IC.BUS.NREG",
    },
    "population": {
        "publisher": "world_bank_wdi",
        "series_id": "SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/SP.POP.TOTL",
    },
    "gdp_pc_growth": {
        "publisher": "world_bank_wdi",
        "series_id": "NY.GDP.PCAP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet",
        "sha256": "3bd65e60a77a1ad1cddeb9847cc579508c7e0f1c5e920c507b6953478f9604cf",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD.ZG?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/NY.GDP.PCAP.KD.ZG",
    },
    "rule_of_law": {
        "publisher": "wgi",
        "series_id": "RuleOfLaw",
        "path": "data/vintages/wgi/RuleOfLaw@2026-04-30T114246Z.parquet",
        "sha256": "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/RuleOfLaw?format=json&source=3",
        "methodology_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators",
    },
}

GATE = {
    "interaction_support_min": 0.25,
    "interaction_refute_max": -0.25,
    "interaction_p_max": 0.10,
    "marginal_support_min": 0.40,
    "marginal_refute_max": -0.40,
    "min_observations": 700,
    "min_countries": 50,
}
FORMULA = (
    "fwd_gdp_pc_growth_3y_avg ~ "
    "log_business_entry_per_million * rule_of_law + "
    "gdp_pc_growth + C(country) + C(year)"
)
TERM = "log_business_entry_per_million:rule_of_law"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_sources() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, source in SOURCES.items():
        path = ROOT / source["path"]
        actual = sha256(path)
        if actual != source["sha256"]:
            raise ValueError(f"pinned data hash mismatch: {source['path']}")
        result[name] = dict(source, vintage_file=source["path"], license="CC-BY-4.0")
        result[name].pop("path")
    return result


def series(name: str) -> pd.DataFrame:
    source = SOURCES[name]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "year", "value"])
    frame = frame.rename(columns={"country_iso3": "country", "value": name})
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[name] = pd.to_numeric(frame[name], errors="coerce")
    frame = frame[
        frame["country"].astype(str).str.fullmatch(r"[A-Z]{3}")
        & ~frame["country"].isin(ORIGINAL_COUNTRIES)
        & frame["year"].between(2006, 2022)
    ].dropna(subset=["country", "year", name])
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country", "year"]).any():
        raise ValueError(f"duplicate country-year in pinned {name} vintage")
    return frame[["country", "year", name]]


def build_panel() -> pd.DataFrame:
    entry = series("business_registrations")
    population = series("population")
    rule = series("rule_of_law")
    growth = series("gdp_pc_growth")
    panel = entry.merge(population, on=["country", "year"], validate="one_to_one")
    panel = panel.merge(rule, on=["country", "year"], validate="one_to_one")
    panel = panel.merge(growth, on=["country", "year"], validate="one_to_one")
    for ahead in (1, 2, 3):
        forward = growth.rename(columns={"gdp_pc_growth": f"growth_t_plus_{ahead}"}).copy()
        forward["year"] -= ahead
        panel = panel.merge(forward, on=["country", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(2006, 2019)].copy()
    panel = panel[(panel["population"] > 0) & (panel["business_registrations"] >= 0)]
    panel["log_business_entry_per_million"] = np.log1p(
        panel["business_registrations"] / panel["population"] * 1_000_000
    )
    panel["fwd_gdp_pc_growth_3y_avg"] = panel[
        ["growth_t_plus_1", "growth_t_plus_2", "growth_t_plus_3"]
    ].mean(axis=1)
    panel = panel.replace([math.inf, -math.inf], np.nan).dropna(
        subset=["log_business_entry_per_million", "fwd_gdp_pc_growth_3y_avg"]
    )
    if set(panel["country"]) & ORIGINAL_COUNTRIES:
        raise AssertionError("old and holdout countries overlap")
    return panel.sort_values(["country", "year"]).reset_index(drop=True)


def preflight() -> tuple[dict[str, Any], pd.DataFrame, dict[str, dict[str, Any]]]:
    sources = verified_sources()
    panel = build_panel()
    n_obs = int(len(panel))
    n_countries = int(panel["country"].nunique())
    years = [int(panel["year"].min()), int(panel["year"].max())] if n_obs else [None, None]
    result = {
        "observations": n_obs,
        "countries": n_countries,
        "treatment_years": years,
        "old_countries_excluded": len(ORIGINAL_COUNTRIES),
        "country_overlap_with_old": 0,
        "passed": n_obs >= GATE["min_observations"] and n_countries >= GATE["min_countries"],
        "gate": {"min_observations": GATE["min_observations"], "min_countries": GATE["min_countries"]},
        "input_paths": [source["vintage_file"] for source in sources.values()],
        "coefficient_estimated": False,
    }
    return result, panel, sources


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def registered_spec_commit() -> str:
    for relative_path in (SPEC_REL, STEELMAN_REL, RUNNER_REL):
        path = ROOT / relative_path
        committed = git("show", f"HEAD:{relative_path}")
        if committed.returncode != 0 or committed.stdout.encode("utf-8") != path.read_bytes():
            raise RuntimeError(f"commit preregistration files before estimation: {relative_path}")
    first = git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = first.stdout.strip().splitlines()
    if first.returncode != 0 or not commits:
        raise RuntimeError("new spec has no first-addition commit")
    return commits[0]


def verdict(coefficient: float, p_value: float, gap: float) -> tuple[str, str]:
    if coefficient >= GATE["interaction_support_min"] and p_value <= GATE["interaction_p_max"] and gap >= GATE["marginal_support_min"]:
        return "SUPPORTED", "all registered positive-interaction and magnitude gates pass"
    if coefficient <= GATE["interaction_refute_max"] and p_value <= GATE["interaction_p_max"] and gap <= GATE["marginal_refute_max"]:
        return "REFUTED", "registered significant negative-interaction and magnitude gates pass"
    return "PARTIAL", "estimable holdout result does not clear support or refutation gates"


def replication_wrapper() -> str:
    return f"""#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call(
    [sys.executable, str(root / {RUNNER_REL!r}), '--run', '--force'], cwd=root
))
"""


def record_inconclusive(
    prereg_commit: str,
    reason: str,
    gate: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    error: Exception | None = None,
) -> dict[str, Any]:
    """Persist an honest non-result without implying a coefficient was estimated."""
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID,
        "verdict": "INCONCLUSIVE",
        "verdict_label": "INCONCLUSIVE",
        "verdict_reason": reason,
        "run_utc": timestamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "template": "panel_fe",
        "preflight": gate,
        "estimate": None,
        "data_status": {
            "variables_missing": [],
            "input_vintages": [source["vintage_file"] for source in sources.values()],
        },
        "error_type": type(error).__name__ if error is not None else None,
        "error_message": str(error) if error is not None else None,
        "limitations": ["No primary coefficient was accepted; this run receives no evidence credit."],
    }
    manifest = {
        "hypothesis_id": HYPOTHESIS_ID,
        "run_utc": timestamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "status": "INCONCLUSIVE",
        "vintages": list(sources.values()),
        "derived_panel": {
            "rows_after_join": gate.get("observations"),
            "countries_after_join": gate.get("countries"),
            "treatment_years": gate.get("treatment_years"),
            "excluded_old_country_count": len(ORIGINAL_COUNTRIES),
        },
    }
    packet = {
        "packet_version": 1,
        "generated_utc": timestamp,
        "hypothesis": {"id": HYPOTHESIS_ID, "path": SPEC_REL, "topic": "institutional_quality"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL, "gate": GATE},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL, "command": f"python3 {RUNNER_REL} --run --force"},
        "verdict": {"raw": "INCONCLUSIVE", "bucket": "inconclusive", "reason": reason},
        "data": {"inputs": list(sources.values())},
        "results": None,
        "limitations": diagnostics["limitations"],
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(
        f"# Result card: {HYPOTHESIS_ID}\n\nVerdict: **INCONCLUSIVE**. {reason}.\n\n"
        "No primary coefficient was accepted or given public evidence credit.\n",
        encoding="utf-8",
    )
    (RUN_DIR / "replication.py").write_text(replication_wrapper(), encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(
        json.dumps({"hypothesis_id": HYPOTHESIS_ID, "verdict": "INCONCLUSIVE", "reason": reason}, indent=2) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(columns=["term", "coefficient", "std_error", "p_value"]).to_parquet(
        RUN_DIR / "coefficients.parquet", index=False
    )
    return {"verdict": "INCONCLUSIVE", "reason": reason, "run_dir": RUN_REL}


def run(force: bool = False) -> dict[str, Any]:
    prereg_commit = registered_spec_commit()
    if RUN_DIR.exists() and not force:
        raise FileExistsError(f"run already exists: {RUN_DIR}; use --force only for explicit replication")
    try:
        gate, panel, sources = preflight()
    except Exception as error:
        return record_inconclusive(
            prereg_commit,
            f"pinned input or coverage preflight failed: {type(error).__name__}: {error}",
            {"passed": False, "coefficient_estimated": False},
            {},
            error,
        )
    if not gate["passed"]:
        return record_inconclusive(
            prereg_commit,
            f"registered data gate failed: {gate['observations']} observations, {gate['countries']} countries",
            gate,
            sources,
        )
    try:
        fit = smf.ols(FORMULA, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country"], "use_correction": True}
        )
        coefficient = float(fit.params[TERM])
        std_error = float(fit.bse[TERM])
        p_value = float(fit.pvalues[TERM])
        ci = [float(value) for value in fit.conf_int().loc[TERM].tolist()]
        if not all(math.isfinite(value) for value in (coefficient, std_error, p_value, *ci)) or std_error <= 0:
            raise ValueError("primary estimator returned nonfinite or zero uncertainty")
        p25_rule = float(panel["rule_of_law"].quantile(0.25))
        p75_rule = float(panel["rule_of_law"].quantile(0.75))
        marginal_gap = coefficient * (p75_rule - p25_rule)
    except Exception as error:
        return record_inconclusive(
            prereg_commit,
            f"primary estimation failed: {type(error).__name__}: {error}",
            gate,
            sources,
            error,
        )
    label, reason = verdict(coefficient, p_value, marginal_gap)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    estimate = {
        "coefficient": coefficient,
        "std_error": std_error,
        "p_value": p_value,
        "ci95": ci,
        "n_obs": int(len(panel)),
        "n_countries": int(panel["country"].nunique()),
        "rule_of_law_p25": p25_rule,
        "rule_of_law_p75": p75_rule,
        "marginal_gap_p75_vs_p25": marginal_gap,
        "r_squared": float(fit.rsquared),
        "method": "OLS country/year FE with country-clustered standard errors",
    }
    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID,
        "verdict": label,
        "verdict_label": label,
        "verdict_reason": reason,
        "run_utc": timestamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "template": "panel_fe",
        "preflight": gate,
        "estimate": estimate,
        "falsification_rule_text": yaml.safe_load((ROOT / SPEC_REL).read_text())["falsification"]["rule"],
        "data_status": {
            "variables_missing": [],
            "input_vintages": [source["vintage_file"] for source in sources.values()],
        },
        "limitations": [
            "Associational geographic holdout, not a causal estimate.",
            "The old 60-country positive result was known when this follow-up was registered.",
            "Registrations and WGI rule of law can reflect changing administrative measurement.",
        ],
    }
    manifest = {
        "hypothesis_id": HYPOTHESIS_ID,
        "run_utc": timestamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "status": label,
        "vintages": list(sources.values()),
        "derived_panel": {
            "rows_after_join": gate["observations"],
            "countries_after_join": gate["countries"],
            "treatment_years": gate["treatment_years"],
            "forward_years": "exact calendar t+1, t+2, and t+3",
            "excluded_old_country_count": len(ORIGINAL_COUNTRIES),
        },
    }
    packet = {
        "packet_version": 1,
        "generated_utc": timestamp,
        "hypothesis": {"id": HYPOTHESIS_ID, "path": SPEC_REL, "topic": "institutional_quality"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL, "gate": GATE},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL, "command": f"python3 {RUNNER_REL} --run --force"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": list(sources.values())},
        "results": estimate,
        "limitations": diagnostics["limitations"],
    }
    card = f"""# Result card: {HYPOTHESIS_ID}

Verdict: **{label}**. {reason}.

## Registered design

This tests the original business-entry by rule-of-law association in countries
outside the old 60-country sample. The old positive result was known at the
time of this follow-up registration. This is an associational geographic
holdout, not a causal policy effect.

- Registration commit: `{prereg_commit}`
- Treatment years: {gate['treatment_years'][0]}–{gate['treatment_years'][1]}
- Sample: {gate['observations']} country-years across {gate['countries']} countries
- Old-sample country overlap: 0
- Estimator: {estimate['method']}
- Outcome: mean real GDP-per-capita growth in exact calendar years t+1 through t+3

## Primary result

- Interaction coefficient: {coefficient:+.4f} (clustered SE {std_error:.4f}; p={p_value:.4g})
- 95% confidence interval: [{ci[0]:+.4f}, {ci[1]:+.4f}]
- Rule-of-law p25/p75: {p25_rule:+.3f} / {p75_rule:+.3f}
- Implied entry-slope gap at rule-of-law p75 versus p25: {marginal_gap:+.4f}

## Interpretation and limits

The frozen thresholds and data gate are in the spec. Business registrations
may reflect filing reforms or formalization rather than productive entry.
Rule of law and growth share potential time-varying confounders. No school
score or public claim is changed by this run alone.
"""
    wrapper = replication_wrapper()
    chart = {
        "hypothesis_id": HYPOTHESIS_ID,
        "annual_country_counts": [
            {"year": int(year), "countries": int(count)}
            for year, count in panel.groupby("year")["country"].nunique().items()
        ],
        "coefficient": coefficient,
        "ci95": ci,
        "registered_support_threshold": GATE["interaction_support_min"],
    }

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(card, encoding="utf-8")
    (RUN_DIR / "replication.py").write_text(wrapper, encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame([{"term": TERM, **estimate}]).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    return {"verdict": label, "reason": reason, "estimate": estimate, "run_dir": RUN_REL}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--preflight", action="store_true")
    command.add_argument("--run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        try:
            result, _, _ = preflight()
        except Exception as error:
            result = {
                "passed": False,
                "coefficient_estimated": False,
                "reason": f"pinned input or coverage preflight failed: {type(error).__name__}: {error}",
            }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1
    else:
        result = run(force=args.force)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
