#!/usr/bin/env python3
"""Exact replay of a precommitted two-outcome WGI rule-of-law holdout family."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS

ROOT = Path(__file__).resolve().parents[1]
IDS = (
    "wgi_rule_of_law_forward_gdp_pc_growth_holdout_v2",
    "wgi_rule_of_law_forward_fixed_capital_growth_holdout_v2",
)
FAMILY_ID = "wgi_rule_of_law_five_year_geographic_holdout_2026_10_10"
REGISTRATION_COMMIT = "e3eacf6978bf8f52fbdcedea8a147729362d745e"
SOURCE_LOCK_COMMIT = "2614ed95857189d7494ff2335bab30d5c6426509"
LOCK_REL = "data/pinned_evidence/wgi_rule_of_law_five_year_geographic_holdout_2026.source.json"
RUNNER_REL = "scripts/run_wgi_rule_of_law_five_year_holdout_2026.py"
YEARS = [2002, 2007, 2012, 2017]
OUTCOMES = {
    IDS[0]: "annualized_real_gdp_pc_log_growth_next_five_years",
    IDS[1]: "mean_real_fixed_capital_growth_next_five_years",
}
CONTROLS = ["log_real_gdp_pc_t", "investment_share_t", "trade_share_t", "dependency_ratio_t"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_series(ref: dict, value_name: str, roster: set[str]) -> pd.DataFrame:
    path = ROOT / ref["path"]
    if not path.is_file() or sha256(path) != ref["sha256"]:
        raise ValueError(f"source unavailable or SHA mismatch: {ref['path']}")
    frame = pq.read_table(path, columns=["country_iso3", "year", "value"]).to_pandas()
    frame = frame.rename(columns={"country_iso3": "country", "value": value_name})
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame = frame[frame["country"].isin(roster)].copy()
    frame[value_name] = pd.to_numeric(frame[value_name], errors="coerce")
    if frame.duplicated(["country", "year"]).any():
        raise ValueError(f"duplicate country-year in {ref['path']}")
    return frame[["country", "year", value_name]]


def load_family() -> tuple[dict, dict, pd.DataFrame]:
    specs = {id: yaml.safe_load((ROOT / f"hypotheses/institutional_quality/{id}.yaml").read_text()) for id in IDS}
    lock = json.loads((ROOT / LOCK_REL).read_text())
    if lock["registration_commit"] != REGISTRATION_COMMIT or lock["hypothesis_ids"] != list(IDS):
        raise ValueError("source lock registration mismatch")
    if lock["family_id"] != FAMILY_ID or lock["family_size"] != 2:
        raise ValueError("source lock family mismatch")
    rosters = [specs[id]["sample"]["countries"] for id in IDS]
    if rosters[0] != rosters[1] or len(rosters[0]) != 131:
        raise ValueError("family roster mismatch")
    roster_sha = hashlib.sha256(json.dumps(rosters[0], separators=(",", ":")).encode()).hexdigest()
    if lock["country_roster_sha256"] != roster_sha:
        raise ValueError("roster SHA mismatch")
    for id in IDS:
        th = specs[id]["falsification"]["threshold"]
        if th["family_id"] != FAMILY_ID or th["family_size"] != 2 or th["treatment_years"] != YEARS:
            raise ValueError("registered family parameters differ")
        for key, ref in th["source_files"].items():
            locked = lock["source_files"][key]
            if ref["path"] != locked["path"] or ref["sha256"] != locked["sha256"]:
                raise ValueError("source lock differs from registration")
    refs = specs[IDS[0]]["falsification"]["threshold"]["source_files"]
    series = {key: read_series(ref, key, set(rosters[0])) for key, ref in refs.items()}
    base = pd.MultiIndex.from_product([rosters[0], YEARS], names=["country", "year"]).to_frame(index=False)
    for key in ("rule_of_law", "government_effectiveness", "gdp_pc", "investment_share", "trade_share", "dependency_ratio"):
        base = base.merge(series[key], on=["country", "year"], how="left", validate="one_to_one")
    base = base.rename(columns={
        "rule_of_law": "rule_of_law_t",
        "government_effectiveness": "government_effectiveness_t",
        "gdp_pc": "gdp_pc_t",
        "investment_share": "investment_share_t",
        "trade_share": "trade_share_t",
        "dependency_ratio": "dependency_ratio_t",
    })
    future = series["gdp_pc"].rename(columns={"gdp_pc": "gdp_pc_t_plus_5"}).copy()
    future["year"] -= 5
    base = base.merge(future, on=["country", "year"], how="left", validate="one_to_one")
    base["log_real_gdp_pc_t"] = np.where(base["gdp_pc_t"] > 0, np.log(base["gdp_pc_t"]), np.nan)
    base[OUTCOMES[IDS[0]]] = np.where(
        (base["gdp_pc_t"] > 0) & (base["gdp_pc_t_plus_5"] > 0),
        100.0 * (np.log(base["gdp_pc_t_plus_5"]) - np.log(base["gdp_pc_t"])) / 5.0,
        np.nan,
    )
    for h in range(1, 6):
        forward = series["fixed_capital_growth"].rename(columns={"fixed_capital_growth": f"fixed_capital_growth_t_plus_{h}"}).copy()
        forward["year"] -= h
        base = base.merge(forward, on=["country", "year"], how="left", validate="one_to_one")
    investment_cols = [f"fixed_capital_growth_t_plus_{h}" for h in range(1, 6)]
    base[OUTCOMES[IDS[1]]] = base[investment_cols].mean(axis=1, skipna=False)
    return specs, lock, base


def sample_for(base: pd.DataFrame, outcome: str, min_blocks_per_country: int) -> pd.DataFrame:
    required = ["rule_of_law_t", *CONTROLS, outcome]
    sample = base.copy()
    for col in required:
        sample = sample[np.isfinite(sample[col])].copy()
    counts = sample.groupby("country").size()
    sample = sample[sample["country"].isin(counts[counts >= min_blocks_per_country].index)].copy()
    return sample.sort_values(["country", "year"]).reset_index(drop=True)


def fit(sample: pd.DataFrame, outcome: str, ge: bool = False) -> dict:
    regressors = ["rule_of_law_t", *CONTROLS]
    if ge:
        regressors.append("government_effectiveness_t")
    panel = sample[["country", "year", outcome, *regressors]].copy()
    if not np.isfinite(panel[regressors].to_numpy(dtype=float)).all():
        raise ValueError("nonfinite sensitivity regressor on fixed primary sample")
    panel = panel.set_index(["country", "year"])
    result = PanelOLS(panel[outcome], panel[regressors], entity_effects=True,
                      time_effects=True, check_rank=True, drop_absorbed=False).fit(
                          cov_type="clustered", cluster_entity=True)
    term = "rule_of_law_t"
    return {
        "outcome": outcome,
        "n_blocks": int(result.nobs),
        "n_countries": int(panel.index.get_level_values("country").nunique()),
        "coefficient": float(result.params[term]),
        "clustered_se": float(result.std_errors[term]),
        "two_sided_p": float(result.pvalues[term]),
        "r2_within": float(result.rsquared_within),
    }


def max_country_treatment_share(sample: pd.DataFrame) -> float:
    panel = sample.set_index(["country", "year"])[["rule_of_law_t"]].copy()
    panel["constant"] = 1.0
    fitted = PanelOLS(panel["rule_of_law_t"], panel[["constant"]],
                      entity_effects=True, time_effects=True).fit()
    squared = fitted.resids.pow(2)
    total = float(squared.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("no identified within-country/year treatment variation")
    return float(squared.groupby(level="country").sum().max() / total)


def render(id: str, spec: dict, lock: dict, base: pd.DataFrame) -> dict[str, bytes]:
    threshold = spec["falsification"]["threshold"]
    outcome = OUTCOMES[id]
    sample = sample_for(base, outcome, threshold["min_blocks_per_country"])
    n_countries = int(sample["country"].nunique())
    range_count = int((sample.groupby("country")["rule_of_law_t"].max()
                       - sample.groupby("country")["rule_of_law_t"].min() >= 0.05).sum())
    diag = {
        "hypothesis_id": id,
        "family_id": FAMILY_ID,
        "family_size": 2,
        "independent_family_count": 1,
        "registration_commit": REGISTRATION_COMMIT,
        "source_lock_commit": SOURCE_LOCK_COMMIT,
        "sample": {"roster_countries": 131, "complete_blocks": int(len(sample)),
                   "complete_countries": n_countries, "countries_with_0_05_rule_of_law_range": range_count,
                   "treatment_years": YEARS, "forward_horizon_years": 5},
        "max_country_residualized_treatment_share": None,
        "primary": None,
        "government_effectiveness_sensitivity": None,
        "gate_failures": [],
        "correction": {"disposition": "descriptive_calibration_only",
                       "school_score_eligible": False, "school_score_credit": 0,
                       "policy_score_eligible": False, "policy_score_credit": 0},
        "evidence_tier_recommendation": "calibration",
    }
    if len(sample) < threshold["min_blocks"]:
        diag["gate_failures"].append("minimum_complete_blocks")
    if n_countries < threshold["min_countries"]:
        diag["gate_failures"].append("minimum_complete_countries")
    if range_count < threshold["min_countries_with_treatment_range_0_05"]:
        diag["gate_failures"].append("minimum_material_rule_of_law_range")
    if not diag["gate_failures"]:
        try:
            diag["max_country_residualized_treatment_share"] = max_country_treatment_share(sample)
            if diag["max_country_residualized_treatment_share"] > threshold["max_country_residualized_treatment_share"]:
                diag["gate_failures"].append("country_treatment_concentration")
            diag["primary"] = fit(sample, outcome)
            try:
                diag["government_effectiveness_sensitivity"] = fit(sample, outcome, ge=True)
            except Exception as exc:
                diag["government_effectiveness_sensitivity"] = {"fit_error": type(exc).__name__}
        except Exception as exc:
            diag["gate_failures"].append(f"primary_fit_{type(exc).__name__}")
    primary = diag["primary"]
    if primary is not None and any(not np.isfinite(primary[key]) for key in ("coefficient", "clustered_se", "two_sided_p")):
        diag["gate_failures"].append("nonfinite_primary_estimate")
    if diag["gate_failures"]:
        verdict = "INCONCLUSIVE_DATA_PENDING"
    elif primary["coefficient"] > 0 and primary["two_sided_p"] <= threshold["p_max"]:
        verdict = "SUPPORTED"
    elif primary["coefficient"] < 0 and primary["two_sided_p"] <= threshold["p_max"]:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    diag["verdict_label"] = verdict
    diag["verdict"] = verdict
    diag["scope_boundary"] = "Two-outcome shared family; descriptive association only; no causal, policy, school, position, or featured credit."
    result_bytes = (json.dumps(diag,indent=2,sort_keys=True,allow_nan=False) + "\n").encode()
    spec_rel = f"hypotheses/institutional_quality/{id}.yaml"
    manifest = {
        "hypothesis_id": id, "status": verdict,
        "preregistration_commit": REGISTRATION_COMMIT,
        "family_id": FAMILY_ID, "family_size": 2,
        "source": {"source_lock_commit": SOURCE_LOCK_COMMIT,
                   "source_lock_manifest": LOCK_REL,
                   "vintages": threshold["source_files"]},
        "runner": RUNNER_REL,
    }
    packet = {
        "packet_version": 1,
        "hypothesis": {"id": id, "path": spec_rel},
        "preregistration": {"commit": REGISTRATION_COMMIT},
        "family": {"id": FAMILY_ID, "size": 2, "independent_family_count": 1,
                   "bonferroni_p_max_per_test": 0.025},
        "source": {"source_lock_commit": SOURCE_LOCK_COMMIT,
                   "source_lock_manifest": LOCK_REL,
                   "vintages": threshold["source_files"], "contains_source_values": False},
        "reproduction": {"runner": RUNNER_REL,
                         "command": f"python3 {RUNNER_REL} --check {id}",
                         "result_sha256": hashlib.sha256(result_bytes).hexdigest()},
        "result": {"verdict": verdict, "gate_failures": diag["gate_failures"],
                   "sample": diag["sample"], "primary": diag["primary"],
                   "government_effectiveness_sensitivity": diag["government_effectiveness_sensitivity"]},
        "scope_boundary": diag["scope_boundary"],
        "correction": diag["correction"],
    }
    p = primary or {}
    card = [f"# Result card — {id}", "", f"**Verdict:** {verdict}", "",
            "## Registered question", "", spec["claim"], "",
            "## Result", "",
            f"- Complete five-year blocks: {len(sample)} across {n_countries} countries.",
            f"- Countries with rule-of-law range at least 0.05: {range_count}.",
            f"- Maximum country share of residualized treatment variation: {diag['max_country_residualized_treatment_share']}.",
            f"- Primary coefficient: {p.get('coefficient')}; country-clustered two-sided p: {p.get('two_sided_p')}.",
            f"- Government-effectiveness sensitivity coefficient: {(diag['government_effectiveness_sensitivity'] or {}).get('coefficient')}.",
            f"- Gate failures: {', '.join(diag['gate_failures']) if diag['gate_failures'] else 'none'}.",
            "", "## Evidence boundary", "", diag["scope_boundary"],
            "The archived 60-country result and the prior market-order panel were known and are not counted as prospective evidence. WGI ratings may follow growth, and omitted capacity or shocks can affect both variables. The capital outcome is total real fixed-capital growth, not private investment.",
            "", "## Custody", "", f"- Registration: `{REGISTRATION_COMMIT}`.",
            f"- Metadata-only source lock: `{SOURCE_LOCK_COMMIT}`.",
            f"- Source manifest: `{LOCK_REL}`. Raw vintages are local and ignored by Git.", ""]
    return {
        "hypothesis.yaml": (ROOT / spec_rel).read_bytes(),
        "diagnostics.json": result_bytes,
        "manifest.yaml": yaml.safe_dump(manifest,sort_keys=False,allow_unicode=True).encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet,sort_keys=False,allow_unicode=True).encode(),
        "result_card.md": "\n".join(card).encode(),
    }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("hypothesis_id", nargs="?", choices=IDS)
    args=parser.parse_args()
    specs, lock, base = load_family()
    ids = (args.hypothesis_id,) if args.hypothesis_id else IDS
    for id in ids:
        files=render(id,specs[id],lock,base)
        out=ROOT / "engine" / "runs" / id
        if args.check:
            mismatch=[name for name,content in files.items() if not (out/name).is_file() or (out/name).read_bytes()!=content]
            if mismatch:
                raise SystemExit(f"{id}: replay mismatch: {', '.join(mismatch)}")
            print(f"{id}: exact replay passed")
        else:
            out.mkdir(parents=True,exist_ok=True)
            for name,content in files.items():
                (out/name).write_bytes(content)
            print(f"{id}: {json.loads(files['diagnostics.json'])['verdict_label']}")


if __name__ == "__main__":
    main()
