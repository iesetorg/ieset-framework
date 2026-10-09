#!/usr/bin/env python3
"""Run eight measured trade-openness holdouts after the nine-test preregistration.

The default preflight checks pinned source hashes and complete-case coverage only.
It never fits a model. --run requires all nine family registrations in HEAD;
--check independently replays an existing run without writing to its directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_trade_openness_measured_endpoint_holdouts_v2.py"
FAMILY_ID = "trade_openness_geographic_holdouts_2026_10_09"
FAMILY_SIZE = 9  # Eight tests here and the separately run private-consumption test.
P_MAX = 0.01  # Bonferroni FWER bound is 9 * 0.01 = 0.09 < 0.10.
MIN_OBSERVATIONS = 1_500
MIN_COUNTRIES = 80
MIN_PAIRS_PER_COUNTRY = 5
OLD_COUNTRIES = frozenset(
    "ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR "
    "IDN IND ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER "
    "PHL POL SWE THA TUR USA VNM ZAF".split()
)
PRIVATE_ID = "trade_openness_private_consumption_geographic_holdout_v2"
PRIVATE_SPEC = f"hypotheses/growth/{PRIVATE_ID}.yaml"
PRIVATE_STEELMAN = f"hypotheses/steelman/{PRIVATE_ID}.md"
PRIVATE_RUNNER_REL = "scripts/run_trade_openness_private_consumption_geographic_holdout_v2.py"

# New ID: (topic, exact outcome source key, original same-commit ID, expected sign).
COHORT = {
    "trade_openness_secondary_enrollment_geographic_holdout_v2":
        ("growth", "secondary_enrollment", "education_quality_trade_openness", "+"),
    "trade_openness_under_five_mortality_geographic_holdout_v2":
        ("healthcare", "under_five_mortality", "food_market_liberalization_nutrition", "-"),
    "trade_openness_internet_use_geographic_holdout_v2":
        ("regulatory", "internet_use", "market_opening_durable_goods_diffusion", "+"),
    "trade_openness_hospital_beds_geographic_holdout_v2":
        ("healthcare", "hospital_beds", "medical_device_trade_openness_outcomes", "+"),
    "trade_openness_high_tech_export_share_geographic_holdout_v2":
        ("trade", "high_tech_export_share", "open_standards_market_diffusion", "+"),
    "trade_openness_gdp_pc_growth_geographic_holdout_v2":
        ("growth", "gdp_pc_growth", "technology_import_openness_productivity", "+"),
    "trade_openness_control_of_corruption_geographic_holdout_v2":
        ("institutional_quality", "control_of_corruption", "trade_openness_governance_discipline", "+"),
    "trade_openness_physician_density_geographic_holdout_v2":
        ("healthcare", "physician_density", "trade_openness_medicine_access", "+"),
}

# (canonical source, frozen local parquet, SHA-256). No latest-file resolution.
VINTAGES = {
    "trade": ("world_bank_wdi:NE.TRD.GNFS.ZS", "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet", "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1"),
    "income": ("world_bank_wdi:NY.GDP.PCAP.KD", "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet", "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f"),
    "rule_of_law": ("wgi:RL.EST", "data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet", "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d"),
    "secondary_enrollment": ("world_bank_wdi:SE.SEC.ENRR", "data/vintages/world_bank_wdi/SE.SEC.ENRR@2026-05-05T204008Z.parquet", "787f29eb93204dbf11dd408449910c28b523376c054734f1fc68d4215b7b2044"),
    "under_five_mortality": ("world_bank_wdi:SH.DYN.MORT", "data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet", "ad63729ccd5d1d4be6f3da5bbcac45b8a2c87d48c063cefeba8f0ddbe4b88f55"),
    "internet_use": ("world_bank_wdi:IT.NET.USER.ZS", "data/vintages/world_bank_wdi/IT.NET.USER.ZS@2026-05-05T203400Z.parquet", "c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8"),
    "hospital_beds": ("world_bank_wdi:SH.MED.BEDS.ZS", "data/vintages/world_bank_wdi/SH.MED.BEDS.ZS@2026-04-30T114635Z.parquet", "314f060add784ee0f788e4e891d1547618cb8069e77946ff6887ea5ba867c046"),
    "high_tech_export_share": ("world_bank_wdi:TX.VAL.TECH.MF.ZS", "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet", "b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994"),
    "gdp_pc_growth": ("world_bank_wdi:NY.GDP.PCAP.KD.ZG", "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet", "3bd65e60a77a1ad1cddeb9847cc579508c7e0f1c5e920c507b6953478f9604cf"),
    "control_of_corruption": ("wgi:CC.EST", "data/vintages/wgi/CC.EST@2026-04-30T114239Z.parquet", "192e9da5c623e2894758bd6cc3fa69f49485edbc06e2150f894bf95666d9d79e"),
    "physician_density": ("world_bank_wdi:SH.MED.PHYS.ZS", "data/vintages/world_bank_wdi/SH.MED.PHYS.ZS@2026-05-05T203455Z.parquet", "dc4fea8a387adb212f254bdcdae60323b694b0a9a18be81c1ec1484fa7bbed33"),
}


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id][0]
    return (
        f"hypotheses/{topic}/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


@cache
def sha256(relative_path: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative_path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_spec(hypothesis_id: str) -> dict[str, Any]:
    spec_path, _, _ = paths(hypothesis_id)
    spec = yaml.safe_load((ROOT / spec_path).read_text(encoding="utf-8"))
    _, outcome, _, sign = COHORT[hypothesis_id]
    threshold = spec["falsification"]["threshold"]
    if spec["hypothesis_id"] != hypothesis_id or spec["status"] != "pre_registered":
        raise ValueError(f"unexpected registration: {spec_path}")
    if spec["sample"]["period"] != [1996, 2023] or spec["claim_direction"] != sign:
        raise ValueError(f"sample or direction changed: {spec_path}")
    if any(threshold[k] != v for k, v in {
        "family_id": FAMILY_ID, "family_size": FAMILY_SIZE, "p_max": P_MAX,
        "min_observations": MIN_OBSERVATIONS, "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
    }.items()):
        raise ValueError(f"fixed decision rule changed: {spec_path}")
    roles = {"treatment": "trade", "outcome": outcome,
             "log_gdp_pc": "income", "rule_of_law": "rule_of_law"}
    for role, name in roles.items():
        source, path, expected = VINTAGES[name]
        pin = threshold["source_files"][role]
        if pin != {"path": path, "sha256": expected}:
            raise ValueError(f"source pin changed: {spec_path}: {role}")
        variable = (spec["variables"]["outcome"][0] if role == "outcome"
                    else spec["variables"]["treatment"][0] if role == "treatment"
                    else spec["variables"]["controls"][0 if role == "log_gdp_pc" else 1])
        if variable["source"] != source:
            raise ValueError(f"source series changed: {spec_path}: {role}")
    return spec


def verified_sources(outcome: str) -> list[dict[str, str]]:
    records = []
    for role, name in (("outcome", outcome), ("treatment", "trade"),
                       ("log_gdp_pc", "income"), ("rule_of_law", "rule_of_law")):
        source, path, expected = VINTAGES[name]
        if sha256(path) != expected:
            raise ValueError(f"pinned source hash mismatch: {path}")
        records.append({"role": role, "source": source, "vintage_file": path, "sha256": expected})
    return records


@cache
def load_series(name: str) -> pd.DataFrame:
    _, relative_path, _ = VINTAGES[name]
    frame = pd.read_parquet(ROOT / relative_path, columns=["country_iso3", "year", "value"])
    frame = frame[
        frame["country_iso3"].astype(str).str.fullmatch(r"[A-Z]{3}")
        & ~frame["country_iso3"].isin(OLD_COUNTRIES)
    ].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[name] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["year"].between(1996, 2023)].dropna(subset=[name])
    frame = frame[np.isfinite(frame[name])].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year in pinned {name} vintage")
    return frame[["country_iso3", "year", name]]


def build_panel(hypothesis_id: str) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    validate_spec(hypothesis_id)
    _, outcome, _, _ = COHORT[hypothesis_id]
    sources = verified_sources(outcome)
    # Predictor and controls are t; outcome is exact t+1. Shift outcome's key,
    # never interpolate a missing year or use a nearest observation.
    outcome_frame = load_series(outcome).copy()
    outcome_frame["year"] -= 1
    panel = load_series("trade").merge(
        load_series("income"), on=["country_iso3", "year"], validate="one_to_one"
    ).merge(load_series("rule_of_law"), on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(1996, 2022) & (panel["income"] > 0)]
    panel = panel.merge(outcome_frame, on=["country_iso3", "year"], validate="one_to_one")
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
    panel["log_gdp_pc"] = np.log(panel["income"])
    panel = panel.rename(columns={outcome: "outcome"})
    panel = panel.replace([math.inf, -math.inf], np.nan).dropna(
        subset=["trade", "log_gdp_pc", "rule_of_law", "outcome"]
    )
    if set(panel["country_iso3"]) & OLD_COUNTRIES:
        raise AssertionError("old and holdout countries overlap")
    panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    return panel, sources


def preflight(hypothesis_id: str) -> tuple[dict[str, Any], pd.DataFrame, list[dict[str, str]]]:
    panel, sources = build_panel(hypothesis_id)
    observations = len(panel)
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": observations,
        "countries": countries,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if observations else [],
        "outcome_years": [int(panel["year"].min()) + 1, int(panel["year"].max()) + 1] if observations else [],
        "excluded_old_countries": len(OLD_COUNTRIES),
        "overlap_with_old_countries": 0,
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "minimum_observations": MIN_OBSERVATIONS,
        "minimum_countries": MIN_COUNTRIES,
        "passed": observations >= MIN_OBSERVATIONS and countries >= MIN_COUNTRIES,
        "coefficient_estimated": False,
    }
    return gate, panel, sources


def registration_commit(hypothesis_id: str) -> str:
    spec_path, _, _ = paths(hypothesis_id)
    files = [RUNNER_REL, PRIVATE_SPEC, PRIVATE_STEELMAN, PRIVATE_RUNNER_REL]
    for case_id in COHORT:
        spec, steelman, _ = paths(case_id)
        files.extend((spec, steelman))
    for relative_path in files:
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"], cwd=ROOT,
            capture_output=True, check=False,
        )
        if committed.returncode or committed.stdout != (ROOT / relative_path).read_bytes():
            raise RuntimeError(f"commit the entire nine-test preregistration before estimation: {relative_path}")
    private = yaml.safe_load((ROOT / PRIVATE_SPEC).read_text(encoding="utf-8"))
    p_threshold = private["falsification"]["threshold"]
    if p_threshold["family_size"] != FAMILY_SIZE or p_threshold["p_max"] != P_MAX:
        raise ValueError("the ninth private-consumption registration has a different family rule")
    first = subprocess.run(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", spec_path],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    commits = first.stdout.strip().splitlines()
    if first.returncode or not commits:
        raise RuntimeError(f"no first-addition commit for {spec_path}")
    return commits[0]


def classify(coefficient: float, p_value: float, expected_sign: str) -> tuple[str, str]:
    if p_value <= P_MAX and (coefficient > 0 if expected_sign == "+" else coefficient < 0):
        return "SUPPORTED", "measured association has the expected sign and clears the nine-test threshold"
    if p_value <= P_MAX and (coefficient < 0 if expected_sign == "+" else coefficient > 0):
        return "REFUTED", "measured association has the opposite sign and clears the nine-test threshold"
    return "PARTIAL", "estimable association does not clear the nine-test directional decision rule"


def estimate_one(hypothesis_id: str) -> tuple[dict[str, Any], list[dict[str, str]], str, str, dict[str, Any] | None]:
    gate, panel, sources = preflight(hypothesis_id)
    if not gate["passed"]:
        return gate, sources, "INCONCLUSIVE", "registered complete-case coverage gate did not pass", None
    try:
        fit = smf.ols(
            "outcome ~ trade + log_gdp_pc + rule_of_law + C(country_iso3) + C(year)",
            data=panel,
        ).fit(cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True})
        coefficient = float(fit.params["trade"])
        std_error = float(fit.bse["trade"])
        p_value = float(fit.pvalues["trade"])
        ci95 = [float(value) for value in fit.conf_int().loc["trade"].tolist()]
        if not all(math.isfinite(value) for value in (coefficient, std_error, p_value, *ci95)):
            raise ValueError("nonfinite primary coefficient or uncertainty")
        if std_error <= 0 or np.linalg.matrix_rank(fit.model.exog) < fit.model.exog.shape[1]:
            raise ValueError("primary fixed-effect design or uncertainty is unidentified")
    except Exception as error:
        return gate, sources, "INCONCLUSIVE", f"primary estimation error: {type(error).__name__}: {error}", None
    _, _, _, sign = COHORT[hypothesis_id]
    verdict, reason = classify(coefficient, p_value, sign)
    estimate = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": int(panel["country_iso3"].nunique()),
        "r_squared": float(fit.rsquared),
        "method": "OLS country/year fixed effects with country-clustered covariance",
    }
    return gate, sources, verdict, reason, estimate


def write_run(
    hypothesis_id: str, prereg_commit: str, gate: dict[str, Any],
    sources: list[dict[str, str]], verdict: str, reason: str, estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    spec_path, steelman_path, run_rel = paths(hypothesis_id)
    _, outcome, old_id, sign = COHORT[hypothesis_id]
    run_dir = ROOT / run_rel
    run_dir.mkdir(parents=True, exist_ok=False)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    limitations = [
        "Associational geographic holdout; no causal trade-policy effect is identified.",
        f"The old {old_id} PARTIAL result was known when the new test was registered.",
        "The nine family tests share trade data and countries; no independent-replication claim is made.",
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "family_id": FAMILY_ID,
        "family_size": FAMILY_SIZE, "family_p_max": P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": [s["vintage_file"] for s in sources]},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": old_id, "old_verdict": "PARTIAL",
        "vintages": sources, "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_path, "topic": COHORT[hypothesis_id][0]},
        "preregistration": {"spec_commit": prereg_commit, "steelman": steelman_path,
                            "gate": {"min_observations": MIN_OBSERVATIONS,
                                     "min_countries": MIN_COUNTRIES,
                                     "family_size": FAMILY_SIZE, "family_p_max": P_MAX}},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {run_rel}/replication.py"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": sources, "old_country_overlap": 0},
        "results": estimate, "limitations": limitations,
    }
    card = (
        f"# Result card: {hypothesis_id}\n\n"
        f"Verdict: **{verdict}**. {reason}.\n\n"
        f"Old study: `{old_id}` (PARTIAL, known at registration).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        f"Held-out sample: {gate['observations']} lagged pairs, {gate['countries']} countries, "
        "zero countries shared with the old study.\n"
        "Estimator: country and treatment-year fixed effects with country-clustered standard errors.\n"
        f"Outcome: {VINTAGES[outcome][0]} at t+1; trade share at t.\n"
        f"Expected sign: {sign}; two-sided p <= {P_MAX} across nine related tests.\n\n"
    )
    if estimate is not None:
        card += (
            f"Primary coefficient: {estimate['coefficient']:+.8g}; "
            f"clustered SE {estimate['std_error']:.8g}; p={estimate['p_value']:.8g}; "
            f"95% CI [{estimate['ci95'][0]:+.8g}, {estimate['ci95'][1]:+.8g}].\n\n"
        )
    card += "This result addresses only the measured association, not the older mechanism or a causal policy effect.\n"
    wrapper = (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of this pinned geographic-holdout result."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--check', {hypothesis_id!r}], cwd=root))\n"
    )
    chart = {"hypothesis_id": hypothesis_id, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None, "family_p_max": P_MAX}
    (run_dir / "hypothesis.yaml").write_bytes((ROOT / spec_path).read_bytes())
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    rows = ([{"term": "trade_openness_pct_gdp_t", **estimate}] if estimate else [])
    pd.DataFrame(rows, columns=["term", "coefficient", "std_error", "p_value", "ci95",
                                "n_obs", "n_countries", "r_squared", "method"]).to_parquet(
        run_dir / "coefficients.parquet", index=False
    )
    return {"hypothesis_id": hypothesis_id, "verdict": verdict, "run_dir": run_rel,
            "estimate": estimate}


def run_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit(hypothesis_id)
    _, _, run_rel = paths(hypothesis_id)
    if (ROOT / run_rel).exists():
        raise FileExistsError(f"run already exists: {run_rel}; use --check for read-only replication")
    gate, sources, verdict, reason, estimate = estimate_one(hypothesis_id)
    return write_run(hypothesis_id, prereg_commit, gate, sources, verdict, reason, estimate)


def check_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit(hypothesis_id)
    _, _, run_rel = paths(hypothesis_id)
    run_dir = ROOT / run_rel
    stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8"))
    gate, sources, verdict, _, estimate = estimate_one(hypothesis_id)
    if stored["preregistration_commit"] != prereg_commit or manifest["preregistration_commit"] != prereg_commit:
        raise AssertionError(f"preregistration commit mismatch: {hypothesis_id}")
    if stored["preflight"] != gate or manifest["vintages"] != sources:
        raise AssertionError(f"pinned data or coverage mismatch: {hypothesis_id}")
    if stored["verdict_label"] != verdict or manifest["status"] != verdict:
        raise AssertionError(f"verdict mismatch: {hypothesis_id}")
    old = stored["estimate"]
    if (old is None) != (estimate is None):
        raise AssertionError(f"estimate-presence mismatch: {hypothesis_id}")
    if estimate is not None:
        for field in ("coefficient", "std_error", "p_value", "r_squared"):
            if not math.isclose(float(old[field]), float(estimate[field]), rel_tol=1e-10, abs_tol=1e-12):
                raise AssertionError(f"{field} mismatch: {hypothesis_id}")
        if len(old["ci95"]) != 2 or len(estimate["ci95"]) != 2:
            raise AssertionError(f"confidence interval shape mismatch: {hypothesis_id}")
        for before, after in zip(old["ci95"], estimate["ci95"]):
            if not math.isclose(float(before), float(after), rel_tol=1e-10, abs_tol=1e-12):
                raise AssertionError(f"confidence interval mismatch: {hypothesis_id}")
        if old["n_obs"] != estimate["n_obs"] or old["n_countries"] != estimate["n_countries"]:
            raise AssertionError(f"sample size mismatch: {hypothesis_id}")
    return {"hypothesis_id": hypothesis_id, "verified": True, "verdict": verdict,
            "observations": gate["observations"], "countries": gate["countries"],
            "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", metavar="HYPOTHESIS_ID", choices=[*COHORT, "all"])
    mode.add_argument("--check", metavar="HYPOTHESIS_ID", choices=[*COHORT, "all"])
    args = parser.parse_args()
    if args.preflight:
        results = {hypothesis_id: preflight(hypothesis_id)[0] for hypothesis_id in COHORT}
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(row["passed"] for row in results.values()) else 1
    ids = list(COHORT) if (args.run or args.check) == "all" else [args.run or args.check]
    results = {hypothesis_id: (run_one(hypothesis_id) if args.run else check_one(hypothesis_id))
               for hypothesis_id in ids}
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
