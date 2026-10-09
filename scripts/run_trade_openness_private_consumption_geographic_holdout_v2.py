#!/usr/bin/env python3
"""Pinned-data geographic holdout for trade openness and private consumption.

--preflight checks only source custody and complete-case coverage. --run
requires the spec, steelman, and runner to match committed Git bytes before
the primary coefficient is estimated. --check refits without writing and
compares the stored packet. The old 40-country sample is excluded.
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
HID = "trade_openness_private_consumption_geographic_holdout_v2"
OLD_HID = "trade_openness_consumer_welfare_1980_2024"
SPEC_REL = f"hypotheses/growth/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
PEER_RUNNER_REL = "scripts/run_trade_openness_measured_endpoint_holdouts_v2.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
OLD_MANIFEST_REL = f"engine/runs/{OLD_HID}/manifest.yaml"
OLD_SPEC_REL = f"hypotheses/growth/{OLD_HID}.yaml"
ORIGINAL_COUNTRIES = frozenset(
    "ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN IND "
    "ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL SWE "
    "THA TUR USA VNM ZAF".split()
)
FAMILY_SPECS = (
    ("growth", "trade_openness_private_consumption_geographic_holdout_v2"),
    ("growth", "trade_openness_secondary_enrollment_geographic_holdout_v2"),
    ("healthcare", "trade_openness_under_five_mortality_geographic_holdout_v2"),
    ("regulatory", "trade_openness_internet_use_geographic_holdout_v2"),
    ("healthcare", "trade_openness_hospital_beds_geographic_holdout_v2"),
    ("trade", "trade_openness_high_tech_export_share_geographic_holdout_v2"),
    ("growth", "trade_openness_gdp_pc_growth_geographic_holdout_v2"),
    ("institutional_quality", "trade_openness_control_of_corruption_geographic_holdout_v2"),
    ("healthcare", "trade_openness_physician_density_geographic_holdout_v2"),
)

# Exact paths and SHA-256 values copied from the old committed run manifest.
# They deliberately do not follow mutable latest-vintage aliases.
SOURCES = {
    "real_household_consumption_pc": {
        "publisher": "world_bank_wdi", "series_id": "NE.CON.PRVT.PC.KD",
        "path": "data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet",
        "sha256": "e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NE.CON.PRVT.PC.KD?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/NE.CON.PRVT.PC.KD",
    },
    "trade_openness_pct_gdp": {
        "publisher": "world_bank_wdi", "series_id": "NE.TRD.GNFS.ZS",
        "path": "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
        "sha256": "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NE.TRD.GNFS.ZS?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/NE.TRD.GNFS.ZS",
    },
    "gdp_pc_constant": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json",
        "methodology_url": "https://data.worldbank.org/indicator/NY.GDP.PCAP.KD",
    },
    "rule_of_law_wgi": {
        "publisher": "wgi", "series_id": "RL.EST",
        "path": "data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet",
        "sha256": "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/RuleOfLaw?format=json&source=3",
        "methodology_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators",
    },
}
FORMULA = (
    "real_household_consumption_pc ~ trade_openness_pct_gdp + "
    "log_gdp_pc_constant + rule_of_law_wgi + C(country) + C(year)"
)
TERM = "trade_openness_pct_gdp"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frozen_spec() -> dict:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    if spec.get("hypothesis_id") != HID or spec.get("version") != 1:
        raise ValueError("new-ID v1 spec mismatch")
    if spec.get("sample", {}).get("period") != [1996, 2023]:
        raise ValueError("registered period changed")
    expected = {
        "real_household_consumption_pc": SOURCES["real_household_consumption_pc"]["series_id"],
        "trade_openness_pct_gdp": SOURCES["trade_openness_pct_gdp"]["series_id"],
        "log_gdp_pc_constant": SOURCES["gdp_pc_constant"]["series_id"],
        "rule_of_law_wgi": SOURCES["rule_of_law_wgi"]["series_id"],
    }
    declared = [
        *spec["variables"]["outcome"], *spec["variables"]["treatment"],
        *spec["variables"]["controls"],
    ]
    for item in declared:
        name = item["name"]
        if name not in expected or item["source"].split(":", 1)[-1] != expected[name]:
            raise ValueError(f"registered source changed for {name}")
    if len(declared) != 4:
        raise ValueError("registered four-series design changed")
    return spec


def gate_from_spec(spec: dict) -> dict[str, Any]:
    gate = dict(spec["falsification"]["threshold"])
    expected_keys = {"expected_sign", "family_id", "family_size", "family_alpha_max", "p_max", "min_observations", "min_countries", "source_files"}
    if set(gate) != expected_keys or gate["expected_sign"] != "+":
        raise ValueError("registered holdout gate changed shape")
    if gate["family_id"] != "trade_openness_geographic_holdouts_2026_10_09":
        raise ValueError("registered nine-test family changed")
    if not (0 < float(gate["p_max"]) <= 0.10 / int(gate["family_size"])):
        raise ValueError("family-wise p threshold exceeds preregistered 0.10 ceiling")
    if int(gate["family_size"]) != 9 or float(gate["p_max"]) * 9 > float(gate["family_alpha_max"]):
        raise ValueError("nine-test Bonferroni family contract failed")
    expected_source_files = {
        "outcome": SOURCES["real_household_consumption_pc"],
        "treatment": SOURCES["trade_openness_pct_gdp"],
        "log_gdp_pc": SOURCES["gdp_pc_constant"],
        "rule_of_law": SOURCES["rule_of_law_wgi"],
    }
    for label, source in expected_source_files.items():
        if gate["source_files"].get(label) != {"path": source["path"], "sha256": source["sha256"]}:
            raise ValueError(f"registered vintage pin changed: {label}")
    if set(gate["source_files"]) != set(expected_source_files):
        raise ValueError("registered vintage set changed")
    return gate


def verify_old_contract() -> None:
    if len(ORIGINAL_COUNTRIES) != 40:
        raise ValueError("old exclusion must contain exactly 40 countries")
    old_spec = yaml.safe_load((ROOT / OLD_SPEC_REL).read_text())
    if set(old_spec["sample"]["countries"]) != ORIGINAL_COUNTRIES:
        raise ValueError("original country sample no longer matches frozen exclusion")
    old_manifest = yaml.safe_load((ROOT / OLD_MANIFEST_REL).read_text())
    vintages = old_manifest["vintages"]
    old_hashes = {(row["vintage_file"], row["sha256"]) for row in vintages.values()}
    if old_hashes != {(row["path"], row["sha256"]) for row in SOURCES.values()}:
        raise ValueError("pinned sources differ from old committed manifest")


def verified_sources() -> list[dict[str, Any]]:
    verify_old_contract()
    rows = []
    for source in SOURCES.values():
        path = ROOT / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise ValueError(f"pinned vintage missing or hash mismatch: {source['path']}")
        row = dict(source)
        row["vintage_file"] = row.pop("path")
        row["license"] = "CC-BY-4.0"
        rows.append(row)
    return rows


def series(name: str) -> pd.DataFrame:
    source = SOURCES[name]
    frame = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "year", "value"])
    frame = frame.rename(columns={"country_iso3": "country", "value": name})
    frame["year"] = pd.to_numeric(frame.year, errors="coerce")
    frame[name] = pd.to_numeric(frame[name], errors="coerce")
    frame = frame[
        frame.country.astype(str).str.fullmatch(r"[A-Z]{3}")
        & ~frame.country.isin(ORIGINAL_COUNTRIES)
        & frame.year.between(1996, 2023)
    ].dropna(subset=["country", "year", name])
    frame["year"] = frame.year.astype(int)
    if frame.duplicated(["country", "year"]).any():
        raise ValueError(f"duplicate country-year in pinned {name}")
    return frame[["country", "year", name]]


def build_panel() -> pd.DataFrame:
    panel = series("real_household_consumption_pc")
    for name in ("trade_openness_pct_gdp", "gdp_pc_constant", "rule_of_law_wgi"):
        panel = panel.merge(series(name), on=["country", "year"], validate="one_to_one")
    panel = panel[panel.gdp_pc_constant > 0].copy()
    panel["log_gdp_pc_constant"] = np.log(panel.gdp_pc_constant)
    panel = panel.replace([math.inf, -math.inf], np.nan).dropna(subset=[
        "real_household_consumption_pc", "trade_openness_pct_gdp",
        "log_gdp_pc_constant", "rule_of_law_wgi",
    ])
    if set(panel.country) & ORIGINAL_COUNTRIES:
        raise AssertionError("old and holdout country sets overlap")
    return panel.sort_values(["country", "year"]).reset_index(drop=True)


def preflight() -> tuple[dict, pd.DataFrame, list[dict[str, Any]]]:
    spec = frozen_spec()
    gate = gate_from_spec(spec)
    sources = verified_sources()
    panel = build_panel()
    count = int(len(panel))
    countries = int(panel.country.nunique())
    result = {
        "observations": count,
        "countries": countries,
        "years": [int(panel.year.min()), int(panel.year.max())] if count else [None, None],
        "old_countries_excluded": len(ORIGINAL_COUNTRIES),
        "country_overlap_with_old": 0,
        "passed": count >= int(gate["min_observations"]) and countries >= int(gate["min_countries"]),
        "gate": {"min_observations": gate["min_observations"], "min_countries": gate["min_countries"]},
        "source_paths": [row["vintage_file"] for row in sources],
        "source_hashes_verified": True,
        "coefficient_estimated": False,
    }
    return result, panel, sources


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def preregistration_commit() -> str:
    family_artifacts = [RUNNER_REL, PEER_RUNNER_REL]
    for topic, hypothesis_id in FAMILY_SPECS:
        family_artifacts.extend([
            f"hypotheses/{topic}/{hypothesis_id}.yaml",
            f"hypotheses/steelman/{hypothesis_id}.md",
        ])
    if len(FAMILY_SPECS) != 9 or len(set(family_artifacts)) != 20:
        raise RuntimeError("nine-test family registration inventory changed")
    for relative in family_artifacts:
        current = ROOT / relative
        committed = git("show", f"HEAD:{relative}")
        if committed.returncode or committed.stdout != current.read_bytes():
            raise RuntimeError(f"commit all nine preregistrations and both runners before estimation: {relative}")
    first = git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = first.stdout.decode().strip().splitlines()
    if first.returncode or not commits:
        raise RuntimeError("new spec has no first-addition commit")
    return commits[0]


def decide(coefficient: float, p_value: float, gate: dict) -> tuple[str, str]:
    cutoff = float(gate["p_max"])
    if coefficient > 0 and p_value <= cutoff:
        return "SUPPORTED", "positive trade-openness coefficient clears frozen family-adjusted threshold"
    if coefficient < 0 and p_value <= cutoff:
        return "REFUTED", "negative trade-openness coefficient clears frozen family-adjusted threshold"
    return "PARTIAL", "estimable holdout result clears neither directional threshold"


def replication_wrapper() -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
raise SystemExit(subprocess.call(
    [sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root
))
'''


def record(prereg: str, spec: dict, gate: dict, check: dict, sources: list[dict],
           verdict: str, reason: str, estimate: dict | None,
           panel: pd.DataFrame | None) -> dict:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    limitations = [
        "Associational geographic holdout; no causal trade-policy claim.",
        "The original 40-country PARTIAL result was known before this registration.",
        "GDP per capita and private consumption share income and price drivers; controls do not remove all confounding.",
        "This is one of nine related trade-openness tests with a shared country pool and family-wise threshold.",
    ]
    diagnostics = {
        "hypothesis_id": HID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": timestamp,
        "runner": RUNNER_REL, "preregistration_commit": prereg,
        "template": "panel_fe", "preflight": check,
        "estimate": estimate,
        "falsification_rule_text": spec["falsification"]["rule"],
        "data_status": {"variables_missing": [],
                        "input_vintages": [row["vintage_file"] for row in sources]},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": timestamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg, "status": verdict,
        "vintages": sources,
        "derived_panel": {
            "rows_after_join": check.get("observations"),
            "countries_after_join": check.get("countries"),
            "years": check.get("years"),
            "excluded_old_country_count": len(ORIGINAL_COUNTRIES),
        },
    }
    packet = {
        "packet_version": 1, "generated_utc": timestamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "growth"},
        "preregistration": {"spec_commit": prereg, "steelman": STEELMAN_REL,
                            "gate": gate},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": sources}, "results": estimate,
        "limitations": limitations,
    }
    card = f'''# Result card: {HID}

Verdict: **{verdict}**. {reason}.

## Registered design

- Registration commit: `{prereg}`
- Sample: {check.get('observations')} complete country-years across {check.get('countries')} countries, {check.get('years')}
- Original 40-country sample overlap: 0
- Estimator: country and year FE, country-clustered standard errors
- Outcome: WDI real household consumption per capita
- Primary term: WDI trade openness as percentage of GDP
- Frozen family: {gate['family_size']} related tests; two-sided p <= {gate['p_max']}

## Primary result

{f"Coefficient {estimate['coefficient']:+.6g}, clustered SE {estimate['std_error']:.6g}, p={estimate['p_value']:.4g}, 95% CI {estimate['ci95']}." if estimate else 'No primary coefficient was accepted.'}

## Interpretation and limits

This geographic holdout measures an association in countries omitted from the old
PARTIAL study. It does not identify a causal welfare effect of trade policy.
'''
    chart = {
        "hypothesis_id": HID, "verdict": verdict,
        "annual_country_counts": [
            {"year": int(year), "countries": int(count)}
            for year, count in panel.groupby("year").country.nunique().items()
        ] if panel is not None else [],
        "coefficient": estimate["coefficient"] if estimate else None,
        "ci95": estimate["ci95"] if estimate else None,
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False))
    (RUN_DIR / "result_card.md").write_text(card)
    (RUN_DIR / "replication.py").write_text(replication_wrapper())
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2, allow_nan=False) + "\n")
    row = [{"term": TERM, **estimate}] if estimate else []
    pd.DataFrame(row, columns=["term", "coefficient", "std_error", "p_value", "ci95", "n_obs", "n_countries", "r_squared", "method"]).to_parquet(
        RUN_DIR / "coefficients.parquet", index=False,
    )
    return {"verdict": verdict, "reason": reason, "run_dir": RUN_REL,
            "estimate": estimate}


def evaluate() -> dict:
    """Compute the registered result without writing any run artifact."""
    prereg = preregistration_commit()
    spec = frozen_spec()
    gate = gate_from_spec(spec)
    try:
        check, panel, sources = preflight()
    except Exception as error:
        reason = f"pinned-input preflight failed: {type(error).__name__}: {error}"
        return dict(prereg=prereg, spec=spec, gate=gate,
                    check={"passed": False, "coefficient_estimated": False},
                    sources=[], verdict="INCONCLUSIVE_DATA_PENDING", reason=reason,
                    estimate=None, panel=None)
    if not check["passed"]:
        reason = f"registered coverage floor failed: {check['observations']} rows, {check['countries']} countries"
        return dict(prereg=prereg, spec=spec, gate=gate, check=check,
                    sources=sources, verdict="INCONCLUSIVE_DATA_PENDING",
                    reason=reason, estimate=None, panel=panel)
    try:
        fit = smf.ols(FORMULA, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel.country, "use_correction": True}
        )
        coefficient = float(fit.params[TERM])
        std_error = float(fit.bse[TERM])
        p_value = float(fit.pvalues[TERM])
        ci95 = [float(value) for value in fit.conf_int().loc[TERM].tolist()]
        if std_error <= 0 or not all(math.isfinite(value) for value in
                                      (coefficient, std_error, p_value, *ci95)):
            raise ValueError("nonfinite or zero-uncertainty primary estimate")
    except Exception as error:
        reason = f"registered primary estimator failed: {type(error).__name__}: {error}"
        return dict(prereg=prereg, spec=spec, gate=gate, check=check,
                    sources=sources, verdict="INCONCLUSIVE_DATA_PENDING",
                    reason=reason, estimate=None, panel=panel)
    verdict, reason = decide(coefficient, p_value, gate)
    estimate = {
        "coefficient": coefficient, "std_error": std_error,
        "p_value": p_value, "ci95": ci95,
        "n_obs": len(panel), "n_countries": int(panel.country.nunique()),
        "r_squared": float(fit.rsquared),
        "method": "OLS country/year FE with country-clustered standard errors",
    }
    return dict(prereg=prereg, spec=spec, gate=gate, check=check,
                sources=sources, verdict=verdict, reason=reason,
                estimate=estimate, panel=panel)


def run(force: bool = False) -> dict:
    if RUN_DIR.exists() and not force:
        raise FileExistsError(f"run exists: {RUN_DIR}; --force is for explicit replication")
    state = evaluate()
    return record(**state)


def check_run() -> dict:
    """Refit and compare stored result, coverage, and custody without writes."""
    if not RUN_DIR.is_dir():
        raise FileNotFoundError(f"run packet missing: {RUN_DIR}")
    state = evaluate()
    diagnostics = json.loads((RUN_DIR / "diagnostics.json").read_text())
    manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text())
    packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text())
    chart = json.loads((RUN_DIR / "chart_data.json").read_text())
    checks = {
        "stored_spec_matches": (RUN_DIR / "hypothesis.yaml").read_bytes() == (ROOT / SPEC_REL).read_bytes(),
        "read_only_wrapper_matches": (RUN_DIR / "replication.py").read_text() == replication_wrapper(),
        "preregistration_commit_matches": diagnostics.get("preregistration_commit") == state["prereg"],
        "falsification_rule_matches": diagnostics.get("falsification_rule_text") == state["spec"]["falsification"]["rule"],
        "stored_estimate_matches_refit": diagnostics.get("estimate") == state["estimate"],
        "stored_verdict_matches_refit": (diagnostics.get("verdict_label") == state["verdict"]
                                          and diagnostics.get("verdict_reason") == state["reason"]),
        "stored_sample_matches_refit": diagnostics.get("preflight") == state["check"],
        "manifest_sources_match_pins": manifest.get("vintages") == state["sources"],
        "manifest_verdict_matches_refit": manifest.get("status") == state["verdict"],
        "manifest_sample_matches_refit": manifest.get("derived_panel", {}).get("rows_after_join") == state["check"].get("observations")
                                          and manifest.get("derived_panel", {}).get("countries_after_join") == state["check"].get("countries"),
        "packet_gate_matches_spec": packet.get("preregistration", {}).get("gate") == state["gate"],
        "packet_estimate_matches_refit": packet.get("results") == state["estimate"],
        "packet_verdict_matches_refit": packet.get("verdict", {}).get("raw") == state["verdict"],
        "chart_coefficient_matches_refit": chart.get("coefficient") == (state["estimate"] or {}).get("coefficient"),
    }
    coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    if state["estimate"] is None:
        checks["stored_coefficients_match_refit"] = coefficients.empty
    else:
        checks["stored_coefficients_match_refit"] = (
            len(coefficients) == 1 and coefficients.iloc[0]["term"] == TERM
            and all(coefficients.iloc[0][name] == value
                    for name, value in state["estimate"].items() if name != "ci95")
            and list(coefficients.iloc[0]["ci95"]) == state["estimate"]["ci95"]
        )
    if not all(checks.values()):
        raise RuntimeError(f"read-only replay mismatch: {[name for name, passed in checks.items() if not passed]}")
    return {"passed": True, "verdict": state["verdict"],
            "observations": state["check"].get("observations"),
            "countries": state["check"].get("countries"),
            "source_hashes_verified": True, "artifacts_written": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument("--preflight", action="store_true")
    commands.add_argument("--run", action="store_true")
    commands.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        try:
            result, _, _ = preflight()
        except Exception as error:
            result = {"passed": False, "coefficient_estimated": False,
                      "reason": f"pinned-input preflight failed: {type(error).__name__}: {error}"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1
    if args.check:
        if args.force:
            parser.error("--force cannot be combined with read-only --check")
        result = check_run()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = run(force=args.force)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
