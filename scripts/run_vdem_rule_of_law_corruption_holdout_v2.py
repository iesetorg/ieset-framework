#!/usr/bin/env python3
"""Exact source-pinned replay of the precommitted V-Dem geographic holdout."""
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
HID = "vdem_rule_of_law_corruption_geographic_holdout_v2"
SPEC_REL = f"hypotheses/institutional_quality/{HID}.yaml"
LOCK_REL = f"data/pinned_evidence/{HID}.source.json"
RUN_REL = f"engine/runs/{HID}"
REGISTRATION_COMMIT = "c3ad46dfac3bbb58aa30696e81cbbd50f4ff2786"
SOURCE_LOCK_COMMIT = "d6d622d961589258c3da1a819dc3f21e05959fbb"
PRIMARY = "political_integrity_t_plus_1"
ROBUSTNESS = {
    "public_sector_integrity_t_plus_1": "v2x_pubcorr",
    "executive_integrity_t_plus_1": "v2x_execorr",
    "low_clientelism_t_plus_1": "v2xnp_client",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources(spec: dict, lock: dict) -> pd.DataFrame:
    threshold = spec["falsification"]["threshold"]
    assert lock["registration_commit"] == REGISTRATION_COMMIT
    assert lock["selected_country_count"] == len(spec["sample"]["countries"]) == 132
    roster = spec["sample"]["countries"]
    roster_sha = hashlib.sha256(json.dumps(roster, separators=(",", ":")).encode()).hexdigest()
    assert lock["selected_country_roster_sha256"] == roster_sha
    for key in ("vdem", "gdp_pc"):
        ref = threshold["source_files"][key]
        source = lock["sources"][key]
        assert ref["path"] == source["path"] and ref["sha256"] == source["sha256"]
        path = ROOT / ref["path"]
        assert path.is_file() and sha256(path) == ref["sha256"], f"source hash mismatch: {path}"

    vp = ROOT / threshold["source_files"]["vdem"]["path"]
    wp = ROOT / threshold["source_files"]["gdp_pc"]["path"]
    cols = ["country_text_id", "year", "v2xcl_rol", "v2x_corr", *ROBUSTNESS.values()]
    vdem = pq.read_table(vp, columns=cols).to_pandas()
    vdem = vdem.rename(columns={"country_text_id": "country"})
    vdem["year"] = pd.to_numeric(vdem["year"], errors="raise").astype(int)
    vdem = vdem[vdem["country"].isin(roster) & vdem["year"].between(1996, 2023)].copy()
    assert not vdem.duplicated(["country", "year"]).any(), "V-Dem duplicate country-year"
    current = vdem[vdem["year"].between(1996, 2022)][["country", "year", "v2xcl_rol"]].copy()
    current = current.rename(columns={"v2xcl_rol": "rule_of_law_t"})
    nxt = vdem[vdem["year"].between(1997, 2023)].drop(columns="v2xcl_rol").copy()
    nxt["year"] -= 1
    outcome_columns = {"v2x_corr": PRIMARY, **{v: k for k, v in ROBUSTNESS.items()}}
    nxt = nxt.rename(columns=outcome_columns)
    for column in outcome_columns.values():
        nxt[column] = 1.0 - pd.to_numeric(nxt[column], errors="coerce")
    wdi = pq.read_table(wp, columns=["country_iso3", "year", "value"]).to_pandas()
    wdi = wdi.rename(columns={"country_iso3": "country", "value": "gdp_pc_t"})
    wdi["year"] = pd.to_numeric(wdi["year"], errors="raise").astype(int)
    wdi = wdi[wdi["country"].isin(roster) & wdi["year"].between(1996, 2022)].copy()
    assert not wdi.duplicated(["country", "year"]).any(), "WDI duplicate country-year"
    data = current.merge(nxt, on=["country", "year"], how="inner", validate="one_to_one")
    data = data.merge(wdi, on=["country", "year"], how="inner", validate="one_to_one")
    data["rule_of_law_t"] = pd.to_numeric(data["rule_of_law_t"], errors="coerce")
    data["gdp_pc_t"] = pd.to_numeric(data["gdp_pc_t"], errors="coerce")
    data = data[(data["gdp_pc_t"] > 0) & np.isfinite(data["gdp_pc_t"])].copy()
    data["log_real_gdp_pc_t"] = np.log(data["gdp_pc_t"])
    for col in ["rule_of_law_t", "log_real_gdp_pc_t", PRIMARY]:
        data = data[np.isfinite(data[col])].copy()
    min_pairs = threshold["min_pairs_per_country"]
    counts = data.groupby("country").size()
    data = data[data["country"].isin(counts[counts >= min_pairs].index)].copy()
    return data.sort_values(["country", "year"]).reset_index(drop=True)


def fit(data: pd.DataFrame, outcome: str) -> dict:
    df = data[["country", "year", outcome, "rule_of_law_t", "log_real_gdp_pc_t"]].copy()
    df[outcome] = pd.to_numeric(df[outcome], errors="coerce")
    df = df[np.isfinite(df[outcome])].set_index(["country", "year"])
    result = PanelOLS(
        df[outcome], df[["rule_of_law_t", "log_real_gdp_pc_t"]],
        entity_effects=True, time_effects=True, check_rank=True,
        drop_absorbed=False,
    ).fit(cov_type="clustered", cluster_entity=True)
    term = "rule_of_law_t"
    return {
        "outcome": outcome,
        "n_observations": int(result.nobs),
        "n_countries": int(df.index.get_level_values("country").nunique()),
        "coefficient": float(result.params[term]),
        "clustered_se": float(result.std_errors[term]),
        "two_sided_p": float(result.pvalues[term]),
        "r2_within": float(result.rsquared_within),
    }


def concentration(data: pd.DataFrame) -> float:
    df = data.set_index(["country", "year"])[["rule_of_law_t"]].copy()
    df["constant"] = 1.0
    result = PanelOLS(df["rule_of_law_t"], df[["constant"]], entity_effects=True,
                      time_effects=True).fit()
    square = result.resids.pow(2)
    total = float(square.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("no identified within-country/year treatment variation")
    return float(square.groupby(level="country").sum().max() / total)


def build() -> dict[str, bytes]:
    spec_bytes = (ROOT / SPEC_REL).read_bytes()
    spec = yaml.safe_load(spec_bytes)
    lock = json.loads((ROOT / LOCK_REL).read_text())
    assert spec["hypothesis_id"] == lock["hypothesis_id"] == HID
    data = load_sources(spec, lock)
    threshold = spec["falsification"]["threshold"]
    n_countries = int(data["country"].nunique())
    diagnostics: dict = {
        "hypothesis_id": HID,
        "registration_commit": REGISTRATION_COMMIT,
        "source_lock_commit": SOURCE_LOCK_COMMIT,
        "sample": {"lagged_pairs": int(len(data)), "countries": n_countries,
                   "predictor_years": [1996, 2022], "outcome_years": [1997, 2023]},
        "primary": None,
        "robustness": [],
        "maximum_country_residualized_treatment_share": None,
        "gate_failures": [],
        "correction": {"disposition": "descriptive_calibration_only",
                       "school_score_eligible": False, "school_score_credit": 0,
                       "policy_score_eligible": False, "policy_score_credit": 0},
        "evidence_tier_recommendation": "calibration",
    }
    if len(data) < threshold["min_observations"]:
        diagnostics["gate_failures"].append("minimum_lagged_pairs")
    if n_countries < threshold["min_countries"]:
        diagnostics["gate_failures"].append("minimum_countries")
    if not diagnostics["gate_failures"]:
        try:
            diagnostics["maximum_country_residualized_treatment_share"] = concentration(data)
            if diagnostics["maximum_country_residualized_treatment_share"] > threshold["max_country_residualized_treatment_share"]:
                diagnostics["gate_failures"].append("country_treatment_concentration")
            diagnostics["primary"] = fit(data, PRIMARY)
            for outcome in ROBUSTNESS:
                try:
                    diagnostics["robustness"].append(fit(data, outcome))
                except Exception as exc:
                    diagnostics["robustness"].append({"outcome": outcome, "fit_error": type(exc).__name__})
        except Exception as exc:
            diagnostics["gate_failures"].append(f"primary_fit_{type(exc).__name__}")

    p = diagnostics["primary"]
    if p is not None and any(not np.isfinite(p[key]) for key in ("coefficient", "clustered_se", "two_sided_p")):
        diagnostics["gate_failures"].append("nonfinite_primary_estimate")
    if diagnostics["gate_failures"]:
        verdict = "INCONCLUSIVE_DATA_PENDING"
    else:
        positives = sum(1 for x in diagnostics["robustness"]
                        if x.get("coefficient") is not None and np.isfinite(x["coefficient"]) and x["coefficient"] > 0)
        diagnostics["positive_robustness_count"] = positives
        if p["coefficient"] > 0 and p["two_sided_p"] <= threshold["p_max"] and positives >= threshold["min_positive_robustness_outcomes"]:
            verdict = "SUPPORTED"
        elif p["coefficient"] < 0 and p["two_sided_p"] <= threshold["p_max"]:
            verdict = "REFUTED"
        else:
            verdict = "PARTIAL"
    diagnostics["verdict_label"] = verdict
    diagnostics["verdict"] = verdict
    diagnostics["scope_boundary"] = "Disjoint-country V-Dem association only; no causal, policy, school, position, or featured credit."
    result_bytes = (json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    manifest = {
        "hypothesis_id": HID, "status": verdict,
        "preregistration_commit": REGISTRATION_COMMIT,
        "source": {"source_lock_commit": SOURCE_LOCK_COMMIT, "source_lock_manifest": LOCK_REL,
                   "vintages": threshold["source_files"]},
        "runner": "scripts/run_vdem_rule_of_law_corruption_holdout_v2.py",
    }
    packet = {
        "packet_version": 1,
        "hypothesis": {"id": HID, "path": SPEC_REL},
        "preregistration": {"commit": REGISTRATION_COMMIT},
        "source": {"source_lock_commit": SOURCE_LOCK_COMMIT, "source_lock_manifest": LOCK_REL,
                   "vintages": threshold["source_files"], "contains_source_values": False},
        "reproduction": {"runner": "scripts/run_vdem_rule_of_law_corruption_holdout_v2.py",
                         "command": "python3 scripts/run_vdem_rule_of_law_corruption_holdout_v2.py --check",
                         "result_sha256": hashlib.sha256(result_bytes).hexdigest()},
        "result": {"verdict": verdict, "gate_failures": diagnostics["gate_failures"],
                   "sample": diagnostics["sample"], "primary": diagnostics["primary"],
                   "robustness": diagnostics["robustness"]},
        "scope_boundary": diagnostics["scope_boundary"],
        "correction": diagnostics["correction"],
    }
    primary = diagnostics["primary"] or {}
    card = [f"# Result card — {HID}", "", f"**Verdict:** {verdict}", "",
            "## Registered question", "", spec["claim"], "",
            "## Observed result", "",
            f"- Complete lagged pairs: {len(data)}; countries: {n_countries}.",
            f"- Maximum country share of residualized rule-of-law variation: {diagnostics['maximum_country_residualized_treatment_share']}.",
            f"- Primary coefficient: {primary.get('coefficient')}; two-sided country-clustered p: {primary.get('two_sided_p')}.",
            f"- Gate failures: {', '.join(diagnostics['gate_failures']) if diagnostics['gate_failures'] else 'none'}.",
            "", "## Robustness outcomes", ""]
    for item in diagnostics["robustness"]:
        card.append(f"- {item['outcome']}: coefficient {item.get('coefficient')}; p {item.get('two_sided_p')}; fit error {item.get('fit_error')}.")
    card += ["", "## Evidence boundary", "", diagnostics["scope_boundary"],
             "The old 40-country result was known before this new registration. V-Dem outcome and predictor indices share an expert-coded source family; reverse causation and common coding can explain this association.",
             "", "## Custody", "", f"- Frozen registration: `{REGISTRATION_COMMIT}`.",
             f"- Metadata-only source lock: `{SOURCE_LOCK_COMMIT}`.",
             f"- Sources: `{LOCK_REL}`; raw vintages are retained locally and excluded from Git.", ""]
    return {
        "hypothesis.yaml": spec_bytes,
        "diagnostics.json": result_bytes,
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
        "result_card.md": "\n".join(card).encode(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exactly compare saved outputs with replay")
    args = parser.parse_args()
    out = ROOT / RUN_REL
    files = build()
    if args.check:
        mismatch = [name for name, content in files.items() if not (out / name).exists() or (out / name).read_bytes() != content]
        if mismatch:
            raise SystemExit(f"replay mismatch: {', '.join(mismatch)}")
        print("exact replay passed")
    else:
        out.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (out / name).write_bytes(content)
        print(json.loads(files["diagnostics.json"])["verdict_label"])


if __name__ == "__main__":
    main()
