#!/usr/bin/env python3
"""Frozen 12-sector GDP-growth to CO2-emissions descriptive family.

Preflight reads WDI GDP-growth values and exact Eurostat sector/country/year
keys, never selected Eurostat CO2 values or null masks. The latter are first
opened by --run/--verify after separate registration and source-lock commits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
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
FAMILY = "wdi_gdp_eurostat_sector_co2_2026_10_10"
RUNNER = "scripts/run_wdi_gdp_eurostat_sector_co2_2026.py"
PREREG = "engine/audits/wdi_gdp_eurostat_sector_co2_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_gdp_eurostat_sector_co2_2026_key_roster.csv"
ROSTER_SHA = "2c5b22762e26f303500ce5840daa5d7839f9e172c83f98b220be83323fe9e96c"
LOCK = "data/pinned_evidence/wdi_gdp_eurostat_sector_co2_2026.manifest.json"
SUMMARY = "engine/audits/wdi_gdp_eurostat_sector_co2_results_2026-10-10.md"
SOURCES = {
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
    "co2": {"publisher": "eurostat", "series_id": "env_air_gge",
        "path": "data/vintages/eurostat/env_air_gge@2026-04-30T115534Z.parquet",
        "sha256": "5597d4f1a75c8c9a91306723772bc8ce4e3df3cfa9af65ce137bc6a3e52d8ba2",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
}
GEO_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
    "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
}
# Mutually non-nested direct-fuel-combustion CRF source sectors. No parent
# aggregate and no gas×sector cross-product is counted as a separate case.
CASES = {
    "CRF1A1A": {"id": "wdi_gdp_eurostat_power_heat_co2_cycle_2026", "label": "public electricity and heat", "key_rows": 664, "material_rows": 575},
    "CRF1A2A": {"id": "wdi_gdp_eurostat_iron_steel_fuel_co2_cycle_2026", "label": "iron and steel fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A2C": {"id": "wdi_gdp_eurostat_chemicals_fuel_co2_cycle_2026", "label": "chemicals fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A2D": {"id": "wdi_gdp_eurostat_pulp_paper_fuel_co2_cycle_2026", "label": "pulp, paper and print fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A2E": {"id": "wdi_gdp_eurostat_food_fuel_co2_cycle_2026", "label": "food, beverages and tobacco fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A2F": {"id": "wdi_gdp_eurostat_nonmetal_minerals_fuel_co2_cycle_2026", "label": "non-metallic minerals fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A2G": {"id": "wdi_gdp_eurostat_other_manufacturing_fuel_co2_cycle_2026", "label": "other manufacturing and construction fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A3A": {"id": "wdi_gdp_eurostat_domestic_aviation_co2_cycle_2026", "label": "domestic aviation fuel combustion", "key_rows": 663, "material_rows": 574},
    "CRF1A3B": {"id": "wdi_gdp_eurostat_road_transport_co2_cycle_2026", "label": "road transport fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A4A": {"id": "wdi_gdp_eurostat_commercial_buildings_co2_cycle_2026", "label": "commercial and institutional fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A4B": {"id": "wdi_gdp_eurostat_residential_buildings_co2_cycle_2026", "label": "residential fuel combustion", "key_rows": 664, "material_rows": 575},
    "CRF1A4C": {"id": "wdi_gdp_eurostat_agriculture_fuel_co2_cycle_2026", "label": "agriculture, forestry and fishing fuel combustion", "key_rows": 664, "material_rows": 575},
}
FIRST_YEAR, LAST_YEAR, MIN_YEARS = 1996, 2018, 10
MAX_ABS_GDP_GROWTH, MATERIAL_GROWTH = 15.0, 1.0
MIN_VALID_ROWS, MIN_VALID_COUNTRIES = 450, 23
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 350, 23
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_ABS_BETA = 0.005
MAX_TOP_ONE_PERCENT, MAX_TOP_COUNTRY = 0.30, 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "causal_credit": 0,
    "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "WDI aggregate real GDP growth is a macro cycle measure, not output of the named CRF sector or a policy treatment.",
    "Eurostat republishes EEA/UNFCCC territorial inventories; CRF codes classify emission sources, not NACE economic sectors or consumption footprints.",
    "The pinned Eurostat Parquet has no retained cell flags. Under EEA-to-Eurostat notation, zero may mean not occurring or included elsewhere; this log specification excludes nonpositive endpoints without interpreting them as verified zero emissions.",
    "The pinned WDI growth observation-status field is blank and does not certify country-specific method continuity.",
    "GDP growth and sector emissions are measured over the same calendar year. Year ordering and fixed effects cannot identify a causal response; energy prices, weather, technology, policy, trade, and offshoring confound the relation.",
    "The 12 CRF categories are non-nested but share macro shocks and inventories. Bonferroni correction is local to this fixed family; archive-wide selection is not corrected.",
    "No causal, policy, school-score, position, or featured credit is permitted.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/energy/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(code: str, case: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": MIN_ABS_BETA,
        "min_valid_rows": MIN_VALID_ROWS, "min_valid_countries": MIN_VALID_COUNTRIES,
        "min_material_change_rows": MIN_MATERIAL_ROWS,
        "min_material_change_countries": MIN_MATERIAL_COUNTRIES,
        "material_growth_min_abs": MATERIAL_GROWTH,
        "max_abs_gdp_growth": MAX_ABS_GDP_GROWTH,
        "min_complete_years_per_country": MIN_YEARS,
        "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share": MAX_TOP_COUNTRY,
        "selected_sector": code, "selected_pollutant": "CO2", "selected_unit": "THS_T",
        "selected_frequency": "A", "expected_key_rows": case["key_rows"],
        "expected_key_countries": 29, "expected_material_key_rows": case["material_rows"],
        "roster_sha256": ROSTER_SHA,
        "source_files": {role: {field: source[field] for field in
            ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False}


def load_roster() -> dict[str, list[tuple[str, int]]]:
    path = ROOT / ROSTER
    raw = path.read_bytes()
    if sha256(path) != ROSTER_SHA or not raw.startswith(b"sector_code,country_iso3,year\n"):
        raise RuntimeError("key-only sector roster header/hash mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    observed = [(row["sector_code"], row["country_iso3"], int(row["year"])) for row in records]
    if observed != sorted(set(observed)) or len(observed) != 7967:
        raise RuntimeError("key-only sector roster order, uniqueness, or size changed")
    result = {code: [] for code in CASES}
    for code, country, year in observed:
        if code not in result or country not in GEO_TO_ISO3.values() or not FIRST_YEAR <= year <= LAST_YEAR:
            raise RuntimeError("unexpected selected sector, geography, or year")
        result[code].append((country, year))
    for code, case in CASES.items():
        if len(result[code]) != case["key_rows"] or len({c for c, _ in result[code]}) != 29:
            raise RuntimeError(f"key-only envelope changed: {code}")
    return result


def validate_specs() -> None:
    roster = load_roster()
    if len(CASES) != 12:
        raise RuntimeError("family denominator changed")
    for code, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        countries = sorted({country for country, _ in roster[code]})
        if (spec.get("hypothesis_id") != case["id"] or spec.get("status") != "pre_registered"
                or spec.get("evidence_type") != "associational"
                or spec.get("claim_direction") != "+"
                or spec.get("steelman") != steelman_rel(case)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != []
                or spec["sample"].get("countries") != countries
                or spec["sample"].get("period") != [FIRST_YEAR, LAST_YEAR]
                or spec["falsification"].get("threshold") != threshold_for(code, case)):
            raise RuntimeError(f"frozen sector spec differs from runner: {code}")


def registration_commit() -> str:
    files = [RUNNER, PREREG, ROSTER]
    for case in CASES.values():
        files += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("family registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    for case in CASES.values():
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contained measured result")
    validate_specs()
    return revision


def check_sources() -> dict[str, dict[str, Any]]:
    selected = {}
    for role, source in SOURCES.items():
        raw = ROOT / source["path"]
        manifest_path = ROOT / source["manifest"]
        if not raw.is_file() or sha256(raw) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched pinned source: {role}")
        if not manifest_path.is_file() or sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"missing or mismatched fetch manifest: {role}")
        entries = yaml.safe_load(manifest_path.read_text()).get("entries", [])
        matches = [entry for entry in entries if entry.get("publisher") == source["publisher"]
            and entry.get("series_id") == source["series_id"]
            and entry.get("parquet_path") == source["path"]
            and entry.get("sha256") == source["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest lacks exact source entry: {role}")
        selected[role] = {**source, "source_url": matches[0].get("source_url"),
            "methodology_url": matches[0].get("methodology_url"),
            "license": matches[0].get("license"), "fetch_utc": matches[0].get("fetch_utc")}
    return selected


def exposure() -> pd.Series:
    raw = pd.read_parquet(ROOT / SOURCES["gdp"]["path"],
        columns=["country_iso3", "year", "value"])
    raw = raw.loc[raw.country_iso3.isin(GEO_TO_ISO3.values())
        & raw.year.between(FIRST_YEAR, LAST_YEAR)].copy()
    if raw.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI GDP-growth country-year key")
    raw["value"] = pd.to_numeric(raw.value, errors="coerce")
    raw = raw.loc[raw.value.notna() & raw.value.abs().le(MAX_ABS_GDP_GROWTH)]
    return raw.set_index(["country_iso3", "year"]).value


def sector_keys() -> dict[str, set[tuple[str, int]]]:
    # Strictly categorical keys/dimensions. The Eurostat value/null column is sealed.
    columns = ["freq", "unit", "airpol", "src_crf", "geo_code", "period"]
    raw = pd.read_parquet(ROOT / SOURCES["co2"]["path"], columns=columns)
    raw = raw.loc[raw.freq.eq("A") & raw.unit.eq("THS_T") & raw.airpol.eq("CO2")
        & raw.src_crf.isin(CASES) & raw.geo_code.isin(GEO_TO_ISO3)].copy()
    raw["country_iso3"] = raw.geo_code.map(GEO_TO_ISO3)
    raw["year"] = pd.to_numeric(raw.period, errors="raise").astype(int)
    if raw.duplicated(["src_crf", "country_iso3", "year"]).any():
        raise RuntimeError("duplicate exact Eurostat CO2 sector-country-year key")
    return {code: set(raw.loc[raw.src_crf.eq(code), ["country_iso3", "year"]]
        .itertuples(index=False, name=None)) for code in CASES}


def expected_roster() -> dict[str, list[tuple[str, int]]]:
    x = exposure()
    keys = sector_keys()
    result = {}
    for code in CASES:
        rows = [(country, year) for country, year in x.index
            if (country, year) in keys[code] and (country, year - 1) in keys[code]]
        counts = pd.Series([country for country, _ in rows]).value_counts()
        result[code] = sorted((country, year) for country, year in rows
            if counts[country] >= MIN_YEARS)
    return result


def preflight() -> dict[str, Any]:
    roster = load_roster()
    if expected_roster() != roster:
        raise RuntimeError("frozen roster differs from GDP-growth values and Eurostat keys")
    x = exposure()
    by_sector = {}
    for code, rows in roster.items():
        material = [(country, year) for country, year in rows
            if abs(float(x[country, year])) >= MATERIAL_GROWTH]
        if len(material) != CASES[code]["material_rows"] or len({c for c, _ in material}) != 29:
            raise RuntimeError(f"material GDP-growth key envelope changed: {code}")
        by_sector[code] = {"key_rows": len(rows), "key_countries": 29,
            "material_treatment_rows": len(material), "material_treatment_countries": 29}
    return {"family_size": len(CASES), "by_sector": by_sector,
        "outcome_values_opened": False, "outcome_null_masks_opened": False,
        "note": "Eurostat category/country-year keys are upper bounds; no sector CO2 cell completeness or positivity was screened."}


def lock_payload(registration: str, selected: dict[str, dict[str, Any]],
                 blind: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
        "sources": selected, "key_only_preflight": blind,
        "statement": "Exact source pins were locked after preregistration and before selected Eurostat CO2 values/nulls were opened."}


def write_source_lock() -> None:
    registration = registration_commit()
    selected = check_sources()
    blind = preflight()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(registration, selected, blind), indent=2, sort_keys=True) + "\n")


def check_source_lock(registration: str, selected: dict[str, dict[str, Any]],
                      blind: dict[str, Any]) -> str:
    revision = first_addition(LOCK)
    if revision == registration:
        raise RuntimeError("source lock was not committed separately")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", registration, revision], cwd=ROOT)
    committed_unchanged(LOCK, revision)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, selected, blind):
        raise RuntimeError("committed source lock differs from frozen pins")
    for case in CASES.values():
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contained measured result")
    return revision


def measured_sector_values() -> dict[str, dict[tuple[str, int], float | None]]:
    # First selected Eurostat numeric/null access, after both chronology commits.
    columns = ["freq", "unit", "airpol", "src_crf", "geo_code", "period", "value"]
    raw = pd.read_parquet(ROOT / SOURCES["co2"]["path"], columns=columns)
    raw = raw.loc[raw.freq.eq("A") & raw.unit.eq("THS_T") & raw.airpol.eq("CO2")
        & raw.src_crf.isin(CASES) & raw.geo_code.isin(GEO_TO_ISO3)].copy()
    raw["country_iso3"] = raw.geo_code.map(GEO_TO_ISO3)
    raw["year"] = pd.to_numeric(raw.period, errors="raise").astype(int)
    if raw.duplicated(["src_crf", "country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected Eurostat CO2 cell")
    raw["value"] = pd.to_numeric(raw.value, errors="coerce")
    result = {}
    for code in CASES:
        selected = raw.loc[raw.src_crf.eq(code), ["country_iso3", "year", "value"]]
        result[code] = {(country, int(year)): float(value) if pd.notna(value) else None
            for country, year, value in selected.itertuples(index=False, name=None)}
    return result


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    values = measured_sector_values()
    x = exposure()
    result = {}
    for code, rows in roster.items():
        panel_rows = []
        invalid = 0
        for country, year in rows:
            before, after = values[code].get((country, year - 1)), values[code].get((country, year))
            if (before is None or after is None or not math.isfinite(before)
                    or not math.isfinite(after) or before <= 0 or after <= 0):
                invalid += 1
                continue
            panel_rows.append({"country_iso3": country, "year": year,
                "x": float(x[country, year]), "y": math.log(after / before)})
        panel = pd.DataFrame(panel_rows, columns=["country_iso3", "year", "x", "y"])
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        panel = panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
        material = panel.x.abs().ge(MATERIAL_GROWTH)
        gate = {"key_only_rows": len(rows), "invalid_or_nonpositive_co2_pairs": invalid,
            "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "material_change_rows": int(material.sum()),
            "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
            "min_complete_years_per_country": MIN_YEARS,
            "outcome_values_read_after_lock": True,
            "source_cell_flags_available": False}
        result[code] = panel, gate
    return result


def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_VALID_ROWS or gate["valid_countries"] < MIN_VALID_COUNTRIES
            or gate["material_change_rows"] < MIN_MATERIAL_ROWS
            or gate["material_change_countries"] < MIN_MATERIAL_COUNTRIES):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen complete-case or material-growth floor failed",
            "gate": gate, "primary": None}
    residual_model = smf.ols("x ~ C(country_iso3) + C(year)", data=panel)
    if np.linalg.matrix_rank(residual_model.exog) != residual_model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "residual exposure design lacks full rank",
            "gate": gate, "primary": None}
    residual_sq = np.square(np.asarray(residual_model.fit().resid, dtype=float))
    total = float(residual_sq.sum())
    if not math.isfinite(total) or total <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "no finite residual GDP-growth variation",
            "gate": gate, "primary": None}
    top_n = max(1, math.ceil(.01 * len(panel)))
    gate["top_one_percent_residual_x_share"] = float(sum(sorted(residual_sq, reverse=True)[:top_n]) / total)
    gate["top_country_residual_x_share"] = float(panel.assign(residual_sq=residual_sq)
        .groupby("country_iso3").residual_sq.sum().max() / total)
    if (gate["top_one_percent_residual_x_share"] > MAX_TOP_ONE_PERCENT
            or gate["top_country_residual_x_share"] > MAX_TOP_COUNTRY):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen residual-GDP-growth concentration gate failed",
            "gate": gate, "primary": None}
    model = smf.ols("y ~ x + C(country_iso3) + C(year)", data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "primary model lacks full rank",
            "gate": gate, "primary": None}
    countries = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
        "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive country-cluster uncertainty",
            "gate": gate, "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), countries - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, countries - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"verdict": "INCONCLUSIVE", "reason": "nonfinite Student t inference",
            "gate": gate, "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": 1 - P_MAX,
        "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": countries, "df_inference": countries - 1,
        "model_rank": int(fit.model.rank),
        "method": "country/year FE OLS; country-cluster CR1; Student t(G-1)"}
    if beta >= MIN_ABS_BETA and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive descriptive association clears frozen size and family-significance gates"
    elif beta <= -MIN_ABS_BETA and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite descriptive association clears frozen size and family-significance gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def payload(code: str, result: dict[str, Any], registration: str,
            lock_commit: str, stamp: str) -> dict[str, Any]:
    case = CASES[code]
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    hid = case["id"]
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
        "verdict_label": verdict, "verdict_reason": result["reason"], "run_utc": stamp,
        "runner": RUNNER, "preregistration_commit": registration,
        "source_lock_commit": lock_commit, "source_lock": LOCK, "template": "panel_fe",
        "preflight": gate, "primary": primary, "p_max_two_sided_bonferroni": P_MAX,
        "meaningful_beta_min_abs": MIN_ABS_BETA,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
        "derived_panel": gate, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hid, "path": spec_rel(case), "topic": "energy"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
            "family_id": FAMILY, "family_size": len(CASES), "key_roster": ROSTER,
            "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
        "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
            "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate, "sector_code": code},
        "results": {"primary": primary}, "limitations": LIMITATIONS,
        "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
        f"Preregistration: `{registration}`; source lock: `{lock_commit}`.\n\n"
        f"WDI real GDP growth in year t; Eurostat CO2 for {case['label']} ({code}), "
        f"log growth from t−1 to t. Complete pairs: {gate['valid_rows']} / "
        f"{gate['valid_countries']} countries; material growth years: "
        f"{gate['material_change_rows']} / {gate['material_change_countries']} countries.\n")
    if primary is not None:
        card += (f"\nBeta={primary['coefficient']:+.6g} log CO2 change per +1 GDP-growth point; "
            f"country-cluster SE={primary['std_error']:.6g}; two-sided t p="
            f"{primary['p_value_two_sided']:.6g}; family-adjusted CI="
            f"{primary['confidence_interval']}.\n")
    card += (f"\nAll 12 non-nested sectors stay in the Bonferroni denominator; "
        f"two-sided p≤{P_MAX:.8f} and |beta|≥{MIN_ABS_BETA:.3f} are required for direction. "
        "This is a contemporaneous macro association with zero causal, policy, school, "
        "position, and featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "sector_code": code,
        "verdict": verdict, "primary": primary}
    coefficients = [{"term": "real_gdp_growth_percent_t", **primary}] if primary is not None else []
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
        "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# Real GDP growth and sectoral CO2: frozen 12-test descriptive result", "",
        f"Preregistration `{registration}`; source lock `{lock_commit}`.",
        f"Twelve mutually non-nested CRF source categories; family alpha 0.01; "
        f"each two-sided p≤{P_MAX:.8f} and |beta|≥{MIN_ABS_BETA:.3f} for direction.", "",
        "| CRF sector | Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |",
        "| --- | --- | ---: | ---: | ---: | ---: |"]
    for code, case in CASES.items():
        result = results[code]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {code}: {case['label']} | **{result['verdict']}** | "
            f"{gate['valid_rows']} / {gate['valid_countries']} | "
            f"{gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |")
    lines += ["", "Beta is same-year log sector CO2 change per +1 percentage-point WDI GDP growth. "
        "The selected Eurostat vintage lacks cell flags; positive-endpoint filtering for logs "
        "cannot identify which zeros represented not occurring versus included elsewhere. "
        "These are descriptive calibrations, not sector policy effects; all causal, policy, "
        "school-score, position, and featured credit is zero.", ""]
    return "\n".join(lines)


def normalize(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: fields differ")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list length differs")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected,
                rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("measured family artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for code, case in CASES.items():
        generated = payload(code, results[code], registration, lock_commit, stamp)
        folder = ROOT / run_rel(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(generated["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(generated["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(generated["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(generated["card"])
        (folder / "replication.py").write_text(generated["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(generated["chart"], indent=2) + "\n")
        pd.DataFrame(generated["coefficients"], columns=["term", "coefficient", "std_error",
            "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
            "n_countries", "df_inference", "model_rank", "method"]).to_parquet(
                folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for code, case in CASES.items():
        folder = ROOT / run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        generated = payload(code, results[code], registration, lock_commit, saved["run_utc"])
        equal_close(saved, generated["diagnostics"], f"{code}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), generated["manifest"], f"{code}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), generated["packet"], f"{code}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), generated["chart"], f"{code}.chart")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
            generated["coefficients"], f"{code}.coefficients")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != generated["card"]
                or (folder / "replication.py").read_text() != generated["wrapper"]):
            raise AssertionError(f"{code}: text artifact differs from replay")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "validate-specs", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    selected = check_sources()
    if args.check_sources:
        print("exact WDI and Eurostat source/manifest hashes match; sector CO2 values unopened")
        return 0
    if args.validate_specs:
        validate_specs()
        print("all 12 registered specs agree with frozen runner and roster")
        return 0
    blind = preflight()
    if args.preflight:
        print(json.dumps(blind, indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        print(f"wrote {LOCK}; commit separately before --run")
        return 0
    registration = registration_commit()
    lock_commit = check_source_lock(registration, selected, blind)
    panels = measured_panels(load_roster())
    results = {code: estimate(*panels[code]) for code in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        print({code: result["verdict"] for code, result in results.items()})
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY,
        {code: result["verdict"] for code, result in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
