#!/usr/bin/env python3
"""Frozen two-test WDI growth to Eurostat in-work poverty study.

Preflight reads WDI treatment values and only Eurostat selector keys. Numeric
Eurostat outcome values and null masks are first accessed by --run/--verify
after separate registration and source-lock commits pass chronology guards.
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
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_gdp_eurostat_inwork_poverty_2026_10_10"
RUNNER = "scripts/run_wdi_gdp_inwork_poverty_2026.py"
PREREG = "engine/audits/wdi_gdp_inwork_poverty_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_gdp_inwork_poverty_2026_key_roster.csv"
ROSTER_SHA = "f04b873741ed2c47656989a281d9bfca59df2c80fcbdd7f43e00edbadec0f3a5"
LOCK = "data/pinned_evidence/wdi_gdp_inwork_poverty_2026.manifest.json"
SUMMARY = "engine/audits/wdi_gdp_inwork_poverty_results_2026-10-10.md"
GDP = "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet"
POVERTY = "data/vintages/eurostat/ilc_iw01@2026-04-30T115759Z.parquet"
SOURCES = {
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
            "path": GDP, "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
            "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
            "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "in_work_poverty": {"publisher": "eurostat", "series_id": "ilc_iw01",
                        "path": POVERTY,
                        "sha256": "100a6bf3f962f53c05133b3e9a7e40f25db36bd03575d3fd7816a4368f1ab246",
                        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
                        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
}
EURO_TO_ISO3 = dict(zip(
    "AT BE BG CH CY CZ DE DK EE EL ES FI FR HR HU IS IT LT LU LV MT NL NO PL PT RO SE SI SK TR".split(),
    "AUT BEL BGR CHE CYP CZE DEU DNK EST GRC ESP FIN FRA HRV HUN ISL ITA LTU LUX LVA MLT NLD NOR POL PRT ROU SWE SVN SVK TUR".split(),
))
CASES = {
    "EMP": {"id": "wdi_gdp_growth_eurostat_employed_inwork_poverty_forward_2026",
            "label": "all employed persons", "key_rows": 383, "key_countries": 30,
            "material_rows": 320, "material_countries": 30, "floor": (280, 25, 200, 25)},
    "SAL": {"id": "wdi_gdp_growth_eurostat_salaried_inwork_poverty_forward_2026",
            "label": "employees", "key_rows": 298, "key_countries": 30,
            "material_rows": 240, "material_countries": 30, "floor": (220, 25, 160, 25)},
}
T_START, T_END, MIN_YEARS = 2005, 2017, 5
MAX_ABS_GROWTH, MATERIAL_GROWTH = 15.0, 1.0
FAMILY_ALPHA, P_MAX, MEANINGFUL_BETA = 0.01, 0.005, 0.1
MAX_TOP_ONE_PERCENT, MAX_TOP_COUNTRY = 0.30, 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "causal_credit": 0,
              "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "WDI real GDP growth is a national-accounts macro measure, not a policy treatment or exogenous shock.",
    "The WDI treatment obs_status column is blank and cannot certify country-specific method continuity.",
    "EU-SILC in-work poverty is relative to national median equivalised disposable income after transfers; absolute gains can leave the relative rate unchanged.",
    "The selected Eurostat parquet has no cell-status or method-break column; no result may be described as break-screened.",
    "UK and Ireland are excluded for historical income-reference-year exceptions; residual timing and survey-method differences may remain.",
    "Growth year t can influence the baseline income year underlying survey t+1; published-year lag and fixed effects do not identify causality.",
    "EMP includes some SAL workers; two correlated tests are corrected locally, not against the full IESET archive.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    revisions = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return revisions[-1]


def frozen_file(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen registered file changed: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted registered file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/labour/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(case: dict[str, Any]) -> dict[str, Any]:
    valid, countries, material, material_countries = case["floor"]
    source_files = {role: {field: SOURCES[role][field]
                           for field in ("path", "sha256", "manifest", "manifest_sha256")}
                    for role in ("gdp", "in_work_poverty")}
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "-",
            "meaningful_beta_min_abs": MEANINGFUL_BETA,
            "min_valid_rows": valid, "min_valid_countries": countries,
            "min_material_change_rows": material,
            "min_material_change_countries": material_countries,
            "material_growth_min_abs": MATERIAL_GROWTH,
            "max_abs_gdp_growth": MAX_ABS_GROWTH,
            "min_years_per_country": MIN_YEARS,
            "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT,
            "max_top_country_residual_x_share": MAX_TOP_COUNTRY,
            "expected_key_rows": case["key_rows"],
            "expected_key_countries": case["key_countries"],
            "roster_sha256": ROSTER_SHA, "source_files": source_files,
            "causal_credit": 0, "policy_score_eligible": False,
            "policy_score_credit": 0, "school_score_eligible": False,
            "school_score_credit": 0, "featured_eligible": False}


def registration_commit() -> str:
    paths = [RUNNER, PREREG, ROSTER]
    for case in CASES.values():
        paths += [spec_rel(case), steelman_rel(case)]
    additions = {first_addition(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = additions.pop()
    for path in paths:
        frozen_file(path, revision)
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen roster hash mismatch")
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains a measured result")
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "associational"
                or spec.get("claim_direction") != "-"
                or spec.get("steelman") != steelman_rel(case)
                or spec.get("covers_claims") != []
                or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != []
                or spec["sample"].get("period") != [T_START, T_END]
                or spec["falsification"].get("threshold") != threshold_for(case)):
            raise RuntimeError(f"frozen hypothesis specification mismatch: {case['id']}")
    return revision


def check_sources(source_root: Path) -> dict[str, dict[str, Any]]:
    selected = {}
    for role, source in SOURCES.items():
        raw, manifest = source_root / source["path"], source_root / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned raw source: {role}")
        if not manifest.is_file() or sha256(manifest) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [entry for entry in entries
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest lacks exact pinned entry: {role}")
        entry = matches[0]
        selected[role] = {**source, "source_url": entry.get("source_url"),
                          "methodology_url": entry.get("methodology_url"),
                          "license": entry.get("license"),
                          "fetch_utc": entry.get("fetch_utc")}
    return selected


def load_roster() -> dict[str, list[tuple[str, int]]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("key-only roster bytes changed")
    raw = pd.read_csv(path)
    if list(raw.columns) != ["study_id", "country_iso3", "year"] or raw.duplicated().any():
        raise RuntimeError("invalid key-only roster columns or duplicate")
    expected = raw.sort_values(["study_id", "country_iso3", "year"]).reset_index(drop=True)
    if not raw.reset_index(drop=True).equals(expected):
        raise RuntimeError("key-only roster order changed")
    result = {}
    for case in CASES.values():
        selected = raw.loc[raw.study_id.eq(case["id"])]
        if len(selected) != case["key_rows"] or selected.country_iso3.nunique() != case["key_countries"]:
            raise RuntimeError(f"key-only roster envelope changed: {case['id']}")
        result[case["id"]] = [(str(c), int(y)) for c, y in selected[["country_iso3", "year"]].itertuples(index=False, name=None)]
    if len(raw) != sum(case["key_rows"] for case in CASES.values()):
        raise RuntimeError("key-only roster has an unknown study")
    return result


def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols("x ~ C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    top_n = max(1, math.ceil(0.01 * len(panel)))
    largest_rows = float(np.sort(squared)[-top_n:].sum() / total)
    largest_country = float(pd.DataFrame({"country": panel.country_iso3.to_numpy(),
                                          "squared": squared}).groupby("country").squared.sum().max() / total)
    return largest_rows, largest_country


def source_keys(source_root: Path) -> tuple[dict[tuple[str, int], float], dict[str, set[tuple[str, int]]]]:
    """Read WDI treatment values; Eurostat keys/dimensions only, never value."""
    exposure = pd.read_parquet(source_root / GDP,
                               columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if len(exposure) != 17556 or not exposure.indicator_id.eq("NY.GDP.MKTP.KD.ZG").all():
        raise RuntimeError("WDI source row or indicator contract changed")
    if not exposure.obs_status.fillna("").eq("").all():
        raise RuntimeError("WDI observation-status semantics changed")
    exposure = exposure.loc[exposure.country_iso3.isin(EURO_TO_ISO3.values())
                            & exposure.year.between(T_START, T_END)].copy()
    if exposure.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI country-year exposure")
    exposure["value"] = pd.to_numeric(exposure.value, errors="coerce")
    exposure = exposure.loc[np.isfinite(exposure.value) & exposure.value.abs().le(MAX_ABS_GROWTH)]
    treatment = {(str(c), int(y)): float(v)
                 for c, y, v in exposure[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    poverty = pd.read_parquet(source_root / POVERTY,
                              columns=["freq", "wstatus", "sex", "age", "unit", "geo_code", "period"])
    if len(poverty) != 65457:
        raise RuntimeError("Eurostat raw row-count contract changed")
    poverty = poverty.loc[poverty.freq.eq("A") & poverty.sex.eq("T")
                          & poverty.age.eq("Y18-64") & poverty.unit.eq("PC")
                          & poverty.geo_code.isin(EURO_TO_ISO3)]
    keys = {}
    for status in CASES:
        selected = poverty.loc[poverty.wstatus.eq(status), ["geo_code", "period"]].copy()
        selected["country_iso3"] = selected.geo_code.map(EURO_TO_ISO3)
        selected["year"] = pd.to_numeric(selected.period).astype(int)
        if selected.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate Eurostat selector key: {status}")
        keys[status] = {(str(c), int(y))
                        for c, y in selected[["country_iso3", "year"]].itertuples(index=False, name=None)}
    return treatment, keys


def key_preflight(source_root: Path) -> dict[str, Any]:
    treatment, outcome_keys = source_keys(source_root)
    frozen = load_roster()
    metrics = {}
    for status, case in CASES.items():
        candidates = sorted(((c, y, x) for (c, y), x in treatment.items()
                             if (c, y + 1) in outcome_keys[status]
                             and (c, y + 2) in outcome_keys[status]),
                            key=lambda row: (row[0], row[1]))
        counts = pd.Series([c for c, _, _ in candidates]).value_counts()
        rows = [(c, y, x) for c, y, x in candidates if counts[c] >= MIN_YEARS]
        selected = [(c, y) for c, y, _ in rows]
        if selected != frozen[case["id"]]:
            raise RuntimeError(f"source-only keys differ from frozen roster: {status}")
        material = [(c, y) for c, y, x in rows if abs(x) >= MATERIAL_GROWTH]
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x"])
        shares = concentration(panel)
        if shares is None or shares[0] > MAX_TOP_ONE_PERCENT or shares[1] > MAX_TOP_COUNTRY:
            raise RuntimeError(f"prelock residual-treatment variation fails: {status}")
        if (len(rows) != case["key_rows"] or len(set(c for c, _, _ in rows)) != case["key_countries"]
                or len(material) != case["material_rows"]
                or len(set(c for c, _ in material)) != case["material_countries"]):
            raise RuntimeError(f"treatment-only sample envelope changed: {status}")
        metrics[status] = {"key_rows": len(rows), "key_countries": case["key_countries"],
                           "material_change_rows": len(material),
                           "material_change_countries": case["material_countries"],
                           "top_one_percent_residual_x_share": shares[0],
                           "top_country_residual_x_share": shares[1]}
    return {"treatment_values_read": True, "outcome_values_read": False,
            "outcome_null_masks_read": False,
            "outcome_selector_keys_only": True,
            "roster_sha256": ROSTER_SHA, "cases": metrics}


def lock_payload(registration: str, selected: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "sources": selected, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    registration = registration_commit()
    selected = check_sources(ROOT)
    preflight = key_preflight(ROOT)
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, selected, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening Eurostat outcome values")


def check_source_lock(registration: str, selected: dict[str, Any], preflight: dict[str, Any]) -> str:
    path = ROOT / LOCK
    if not path.is_file() or json.loads(path.read_text()) != lock_payload(registration, selected, preflight):
        raise RuntimeError("source lock differs from frozen source selection or preregistration")
    revision = first_addition(LOCK)
    if revision == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, revision],
                                                   cwd=ROOT).returncode:
        raise RuntimeError("source-lock commit must descend separately from registration")
    frozen_file(LOCK, revision)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return revision


def finite_rate(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) and 0 <= numeric <= 100 else None


def measured_panels(source_root: Path) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First access to Eurostat selected numeric outcomes and their null masks."""
    treatment, _ = source_keys(source_root)
    roster = load_roster()
    frame = pd.read_parquet(source_root / POVERTY,
                            columns=["freq", "wstatus", "sex", "age", "unit", "geo_code", "period", "value"])
    frame = frame.loc[frame.freq.eq("A") & frame.sex.eq("T")
                      & frame.age.eq("Y18-64") & frame.unit.eq("PC")
                      & frame.geo_code.isin(EURO_TO_ISO3)]
    result = {}
    for status, case in CASES.items():
        selected = frame.loc[frame.wstatus.eq(status), ["geo_code", "period", "value"]].copy()
        selected["country_iso3"] = selected.geo_code.map(EURO_TO_ISO3)
        selected["year"] = pd.to_numeric(selected.period).astype(int)
        if selected.duplicated(["country_iso3", "year"]).any():
            raise RuntimeError(f"duplicate selected outcome key: {status}")
        values = {(str(c), int(y)): finite_rate(v)
                  for c, y, v in selected[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
        rows = []
        missing = 0
        for country, year in roster[case["id"]]:
            baseline, forward = values.get((country, year + 1)), values.get((country, year + 2))
            if baseline is None or forward is None:
                missing += 1
                continue
            rows.append({"country_iso3": country, "year": year,
                         "x": treatment[(country, year)], "baseline_rate": baseline,
                         "y": forward - baseline})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "baseline_rate", "y"])
        pre_floor = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        material = panel.x.abs().ge(MATERIAL_GROWTH)
        gate = {"key_only_roster_rows": len(roster[case["id"]]),
                "invalid_or_missing_endpoint_pairs": missing,
                "complete_pairs_before_five_year_country_floor": pre_floor,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "material_change_rows": int(material.sum()),
                "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "outcome_values_read_after_lock": True,
                "outcome_break_flags_available": False}
        result[status] = panel, gate
    return result


def diagnostic_fit(panel: pd.DataFrame, formula: str) -> dict[str, Any]:
    if len(panel) < 40 or panel.country_iso3.nunique() < 20:
        return {"estimable": False, "reason": "diagnostic sample too small"}
    model = smf.ols(formula, data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"estimable": False, "reason": "diagnostic design lacks full rank"}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"estimable": False, "reason": "diagnostic uncertainty invalid"}
    g = int(panel.country_iso3.nunique())
    p = float(2 * student_t.sf(abs(beta / se), g - 1))
    if not math.isfinite(p):
        return {"estimable": False, "reason": "diagnostic p value invalid"}
    return {"estimable": True, "coefficient": beta, "std_error": se,
            "p_value_two_sided": p,
            "n_rows": len(panel), "n_countries": g}


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    floor_n, floor_c, floor_m, floor_mc = case["floor"]
    if (gate["valid_rows"] < floor_n or gate["valid_countries"] < floor_c
            or gate["material_change_rows"] < floor_m
            or gate["material_change_countries"] < floor_mc):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen complete-case or material-growth floor failed",
                "primary": None, "diagnostics": {}}
    shares = concentration(panel)
    if shares is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "no finite residual GDP-growth variation",
                "primary": None, "diagnostics": {}}
    gate["top_one_percent_residual_x_share"], gate["top_country_residual_x_share"] = shares
    if shares[0] > MAX_TOP_ONE_PERCENT or shares[1] > MAX_TOP_COUNTRY:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen residual-growth concentration gate failed",
                "primary": None, "diagnostics": {}}
    model = smf.ols("y ~ x + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "primary fixed-effect design lacks full rank",
                "primary": None, "diagnostics": {}}
    g = int(panel.country_iso3.nunique())
    if g < 20:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "fewer than 20 country clusters",
                "primary": None, "diagnostics": {}}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite or nonpositive country-cluster uncertainty",
                "primary": None, "diagnostics": {}}
    p = float(2 * student_t.sf(abs(beta / se), g - 1))
    critical = float(student_t.ppf(0.9975, g - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "nonfinite Student t inference",
                "primary": None, "diagnostics": {}}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.995,
               "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": g, "df_inference": g - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS, country-cluster CR1, Student t(G-1)"}
    if beta <= -MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "negative descriptive association clears frozen size and family-adjusted p gates"
    elif beta >= MEANINGFUL_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite descriptive association clears frozen size and family-adjusted p gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    diagnostics = {
        "exclude_2008_2009": diagnostic_fit(panel.loc[~panel.year.isin([2008, 2009])],
                                             "y ~ x + C(country_iso3) + C(year)"),
        "baseline_rate_adjusted": diagnostic_fit(panel,
                                                  "y ~ x + baseline_rate + C(country_iso3) + C(year)"),
    }
    return {"gate": gate, "verdict": verdict, "reason": reason,
            "primary": primary, "diagnostics": diagnostics}


def artifact_payload(status: str, case: dict[str, Any], result: dict[str, Any],
                     registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    inputs = {role: SOURCES[role] for role in ("gdp", "in_work_poverty")}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "labour"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 2,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": inputs, "sample": gate},
              "results": {"primary": primary, "diagnostic_only": result["diagnostics"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe",
                   "preflight": gate, "primary": primary,
                   "diagnostic_only": result["diagnostics"],
                   "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": MEANINGFUL_BETA,
                   "data_status": {"variables_missing": [], "input_vintages": list(inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(inputs.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
            f"Exposure: real GDP growth in year t; outcome: EU-SILC in-work poverty for {case['label']}, "
            f"survey t+2 minus t+1. Key-only upper bound: {case['key_rows']} country-years / "
            f"{case['key_countries']} countries. Complete pairs: {gate['valid_rows']} / "
            f"{gate['valid_countries']}; material growth years: {gate['material_change_rows']} / "
            f"{gate['material_change_countries']}.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} poverty-rate points per +1 GDP-growth point; "
                 f"country-cluster SE={primary['std_error']:.6g}; two-sided t p="
                 f"{primary['p_value_two_sided']:.6g}; 99.5% CI={primary['confidence_interval']}.\n")
    card += ("\nTwo prespecified overlapping outcomes; Bonferroni family alpha 0.01, each "
             "two-sided p <= 0.005 and |beta| >= 0.1 required for direction. "
             "EU-SILC income timing is approximate and the vintage lacks cell-level break flags. "
             "Descriptive calibration only; no causal, policy, school, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "real_gdp_growth_percent_t", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart,
            "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Real GDP growth and subsequent in-work poverty: two-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Both tests stay in one Bonferroni family (alpha 0.01; each two-sided p <= 0.005).",
             "", "| Population | Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for status, case in CASES.items():
        result = results[status]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |")
    lines += ["", "Beta measures survey-year poverty-rate change in percentage points per +1 GDP-growth percentage point. Negative is the frozen prediction.",
              "EU-SILC income-reference timing and unavailable cell break flags limit interpretation. Earlier IESET poverty and growth cases are disclosed in the preregistration. These are descriptive calibrations with zero causal, policy, school, position, and featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("one or more measured family artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for status, case in CASES.items():
        payload = artifact_payload(status, case, results[status], registration, lock_commit, stamp)
        folder = ROOT / run_rel(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
        pd.DataFrame(payload["coefficients"], columns=[
            "term", "coefficient", "std_error", "p_value_two_sided", "confidence_level",
            "confidence_interval", "n_rows", "n_countries", "df_inference", "model_rank",
            "method"]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def normalize_arrow(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize_arrow(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize_arrow(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_arrow(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize_arrow(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
                                                               rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for status, case in CASES.items():
        folder = ROOT / run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(status, case, results[status], registration, lock_commit, saved["run_utc"])
        equal_close(saved, payload["diagnostics"], f"{status}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], f"{status}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], f"{status}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], f"{status}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{status}: text artifact mismatch")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                    payload["coefficients"], f"{status}.coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT,
                        help="Only for read-only check-sources/preflight while staged outside the checkout")
    args = parser.parse_args()
    if args.source_root != ROOT and not (args.check_sources or args.preflight):
        parser.error("--source-root override is restricted to read-only checks")
    selected = check_sources(args.source_root)
    if args.check_sources:
        print("WDI GDP and Eurostat poverty source SHA pins match; Eurostat values unopened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(args.source_root), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    preflight = key_preflight(ROOT)
    lock_commit = check_source_lock(registration, selected, preflight)
    panels = measured_panels(ROOT)
    results = {status: estimate(*panels[status], CASES[status]) for status in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for status, result in results.items():
            print(status, result["verdict"], result["reason"])
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY,
          {status: result["verdict"] for status, result in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
