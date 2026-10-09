#!/usr/bin/env python3
"""Source-pinned, prospective temporal youth-unemployment calibration.

--preflight reads source keys and categorical dimensions only. --extract-slice
may read selected magnitudes only after the spec/steelman/runner first-addition
commit. --run requires a separately committed, byte-verified selected slice.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ID = "minimum_wage_median_youth_unemployment_2020_2024_v2"
OLD_ID = "minimum_wage_youth_unemployment_tradeoff"
OLD_COMMIT = "aaf546211593c42dc91f81d0bca349bf9f8c876e"
SPEC_REL = f"hypotheses/labour/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUNNER_REL = f"scripts/run_{ID}.py"
SLICE_REL = f"data/derived/{ID}_source_slice.json"
RUN_REL = f"engine/runs/{ID}"
MANIFEST_REL = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
ROSTER = tuple("AUS BEL BGR CAN CHL COL CRI CZE DEU ESP EST FRA GBR GRC HRV HUN IRL ISR JPN KOR LTU LVA MEX NLD NZL POL PRT ROU SVK SVN TUR USA".split())
YEARS = tuple(range(2020, 2025))
FAMILY_ID = "direct_labour_temporal_followups_2026_10_09"
FAMILY_SIZE, FAMILY_ALPHA, P_MAX = 5, 0.05, 0.01
MIN_OBS, MIN_COUNTRIES, MIN_YEARS = 100, 24, 3
SENS_MIN_OBS, SENS_MIN_COUNTRIES = 72, 18
MW_COL = "minimum_wage_median_aggregation_pct"
YOUTH_COL = "youth_unemployment_rate_pct"
GDP_COL = "real_gdp_growth_pct"
SOURCE_FILES = {
    "minimum_wage": {
        "path": "data/vintages/oecd/MWUSD@2026-05-05T195455Z.parquet",
        "sha256": "d4da2c942e3a714a6392a0a6f3ff831a4431caff0b965b8f93f6544f5c223ddc",
        "publisher": "oecd", "series_id": "MWUSD",
        "source_url": "https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_EARNINGS@MIN2AVE,1.0/all?format=csvfilewithlabels",
        "license": "OECD standard permissions (attribution required)",
    },
    "youth_unemployment": {
        "path": "data/vintages/ilostat/UNE_2EAP_SEX_AGE_RT_A@2026-05-05T195424Z.parquet",
        "sha256": "dcc17617c0ef8f037fc414944d01aeab7a0a71370576b29ff416de18c5348990",
        "publisher": "ilostat", "series_id": "UNE_2EAP_SEX_AGE_RT_A",
        "source_url": "https://rplumber.ilo.org/data/indicator/?id=UNE_2EAP_SEX_AGE_RT_A&format=.csv",
        "license": "cc_by_4_0",
    },
    "real_gdp_growth": {
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KD.ZG?format=json",
        "license": "CC-BY-4.0",
    },
}
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
COEFFICIENT_COLUMNS = ("term", "coefficient", "std_error", "p_value", "ci_family",
                       "n_obs", "n_countries", "r_squared", "method")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def first_addition(relative: str) -> str:
    result = subprocess.run(["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
                            cwd=ROOT, capture_output=True, text=True)
    commits = result.stdout.strip().splitlines()
    if result.returncode or len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit: {relative}")
    return commits[0]


def verify_old() -> None:
    old = yaml.safe_load(git_show(OLD_COMMIT, f"hypotheses/labour/{OLD_ID}.yaml"))
    diagnostic = json.loads(git_show(OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"))
    runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode("utf-8")
    if (old["sample"]["period"] != [1990, 2019]
            or old["variables"]["outcome"][0]["source"] != "ilostat:UNE_2EAP_SEX_AGE_RT_A"
            or old["variables"]["treatment"][0]["source"] != "oecd:MWUSD"
            or diagnostic["estimate"].get("n_obs") != 246
            or diagnostic["estimate"].get("n_countries") != 18
            or "out = out[out[\"year\"] <= int(period[1])]" not in runner
            or "out = out.groupby([\"country_iso3\", \"year\"], as_index=False)[\"value\"].mean()" not in runner):
        raise ValueError("old temporal boundary or dimension-mixing evidence differs")


def verify_spec() -> dict[str, Any]:
    verify_old()
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": FAMILY_ID, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX, "min_observations": MIN_OBS,
        "min_countries": MIN_COUNTRIES, "min_years_per_country": MIN_YEARS,
        "sensitivity_years": [2021, 2024],
        "sensitivity_min_observations": SENS_MIN_OBS,
        "sensitivity_min_countries": SENS_MIN_COUNTRIES,
        "old_hypothesis_id": OLD_ID, "old_run_commit": OLD_COMMIT,
        "old_registered_period": [1990, 2019], "old_n_obs": 246,
        "old_n_countries": 18, "old_fitted_keys_saved": False,
        "fixed_key_upper_bound": 160, "fixed_roster_size": 32,
        "school_score_eligible": False, "school_score_credit": 0,
        "source_manifest": {"path": MANIFEST_REL, "sha256": MANIFEST_SHA},
        "source_files": {role: {k: pin[k] for k in ("path", "sha256", "publisher", "series_id")}
                         for role, pin in SOURCE_FILES.items()},
    }
    variables = spec["variables"]
    if (threshold != expected or spec.get("hypothesis_id") != ID
            or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("claim_direction") != "+"
            or spec["sample"]["countries"] != list(ROSTER)
            or spec["sample"]["period"] != [2020, 2024]
            or spec["scope"]["countries"] != list(ROSTER)
            or spec["scope"]["period"] != [2020, 2024]
            or spec["estimator"]["template"] != "panel_fe"
            or spec["estimator"]["fixed_effects"] != ["country", "year"]
            or spec["estimator"]["clustering"] != "country"
            or [(x["name"], x["source"]) for x in variables["outcome"]]
            != [(YOUTH_COL, "ilostat:UNE_2EAP_SEX_AGE_RT_A")]
            or [(x["name"], x["source"]) for x in variables["treatment"]]
            != [(MW_COL, "oecd:MWUSD")]
            or [(x["name"], x["source"]) for x in variables["controls"]]
            != [(GDP_COL, "world_bank_wdi:NY.GDP.MKTP.KD.ZG")]
            or spec.get("steelman") != STEELMAN_REL
            or any(spec.get(key) != [] for key in ("covers_claims", "linked_hypotheses", "linked_conditions"))):
        raise ValueError("frozen youth-only design differs from runner")
    return spec


def verify_sources() -> None:
    manifest = ROOT / MANIFEST_REL
    if sha256(manifest) != MANIFEST_SHA or git_show("HEAD", MANIFEST_REL) != manifest.read_bytes():
        raise ValueError("publisher manifest changed")
    entries = yaml.safe_load(manifest.read_text(encoding="utf-8"))["entries"]
    for role, pin in SOURCE_FILES.items():
        path = ROOT / pin["path"]
        if not path.is_file() or sha256(path) != pin["sha256"]:
            raise ValueError(f"pinned source absent or changed: {role}")
        if not any(all(row.get(key) == pin[key] for key in
                       ("publisher", "series_id", "source_url", "sha256", "license"))
                   and row.get("parquet_path") == pin["path"] for row in entries):
            raise ValueError(f"publisher manifest row differs: {role}")
    gdp = SOURCE_FILES["real_gdp_growth"]["path"]
    if git_show("HEAD", gdp) != (ROOT / gdp).read_bytes():
        raise ValueError("tracked GDP-control vintage changed")


def key_only_preflight() -> dict[str, Any]:
    import pyarrow.parquet as pq
    verify_spec()
    verify_sources()
    mw = pq.read_table(ROOT / SOURCE_FILES["minimum_wage"]["path"],
                       columns=["REF_AREA", "period", "MEASURE", "UNIT_MEASURE",
                                "AGGREGATION_OPERATION", "PAY_PERIOD", "PRICE_BASE", "SEX"]).to_pydict()
    ilo = pq.read_table(ROOT / SOURCE_FILES["youth_unemployment"]["path"],
                        columns=["country_iso3", "year", "indicator", "sex", "classif1", "source"]).to_pydict()
    gdp = pq.read_table(ROOT / SOURCE_FILES["real_gdp_growth"]["path"],
                        columns=["country_iso3", "year", "indicator_id"]).to_pydict()
    mw_keys = [(a, int(y)) for a, y, measure, unit, agg, pay, price, sex in zip(
        mw["REF_AREA"], mw["period"], mw["MEASURE"], mw["UNIT_MEASURE"],
        mw["AGGREGATION_OPERATION"], mw["PAY_PERIOD"], mw["PRICE_BASE"], mw["SEX"])
        if a in ROSTER and str(y).isdigit() and int(y) in YEARS
        and (measure, unit, agg, pay, price, sex)
        == ("MR_WG_FT", "PT_WG_A_SAL_FT", "MEDIAN", "_Z", "_Z", "_Z")]
    ilo_keys = [(a, int(y)) for a, y, indicator, sex, age, source in zip(
        ilo["country_iso3"], ilo["year"], ilo["indicator"], ilo["sex"],
        ilo["classif1"], ilo["source"])
        if a in ROSTER and isinstance(y, int) and y in YEARS
        and (indicator, sex, age) == ("UNE_2EAP_SEX_AGE_RT", "SEX_T", "AGE_YTHADULT_Y15-24")
        and str(source).startswith("XA:")]
    gdp_keys = [(a, int(y)) for a, y, indicator in zip(
        gdp["country_iso3"], gdp["year"], gdp["indicator_id"])
        if a in ROSTER and isinstance(y, int) and y in YEARS
        and indicator == "NY.GDP.MKTP.KD.ZG"]
    fixed = {(a, y) for a in ROSTER for y in YEARS}
    sets = [set(mw_keys), set(ilo_keys), set(gdp_keys)]
    result = {
        "hypothesis_id": ID,
        "key_only": True, "magnitudes_inspected": False, "null_masks_inspected": False,
        "key_rows": {"minimum_wage": len(mw_keys), "youth_unemployment": len(ilo_keys),
                     "real_gdp_growth": len(gdp_keys)},
        "unique_keys": {"minimum_wage": len(sets[0]), "youth_unemployment": len(sets[1]),
                        "real_gdp_growth": len(sets[2])},
        "fixed_roster_keys": len(fixed), "source_key_intersection": len(set.intersection(*sets)),
        "old_fit_observations": 246, "old_fit_countries": 18,
        "old_registered_end_year": 2019, "heldout_first_year": 2020,
        "actual_old_fit_country_ids_saved": False,
    }
    result["passed"] = all(keys == fixed and len(keys) == len(fixed) for keys in sets)
    return result


def registration_commit() -> str:
    additions = []
    for relative in REGISTRATION_FILES:
        current = (ROOT / relative).read_bytes()
        if git_show("HEAD", relative) != current:
            raise RuntimeError(f"commit unchanged preregistration before value access: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, and runner must first appear in one commit")
    commit = additions[0]
    for relative in REGISTRATION_FILES:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registered bytes changed after first addition: {relative}")
    if git_show(commit, MANIFEST_REL) != (ROOT / MANIFEST_REL).read_bytes():
        raise RuntimeError("publisher manifest changed after preregistration")
    for role, pin in SOURCE_FILES.items():
        if role == "real_gdp_growth" and git_show(commit, pin["path"]) != (ROOT / pin["path"]).read_bytes():
            raise RuntimeError("tracked GDP source changed after preregistration")
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", SLICE_REL, RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if listed.returncode or listed.stdout.strip():
        raise RuntimeError("selected values or result artifacts existed in preregistration commit")
    return commit


def finite_or_none(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def selected_slice(commit: str) -> dict[str, Any]:
    """First value access: call only after registration_commit and source checks."""
    import pandas as pd
    key_only = key_only_preflight()
    if not key_only["passed"]:
        raise ValueError("fixed source-key gate failed")
    paths = {role: ROOT / pin["path"] for role, pin in SOURCE_FILES.items()}
    mw = pd.read_parquet(paths["minimum_wage"], columns=[
        "REF_AREA", "period", "MEASURE", "UNIT_MEASURE", "AGGREGATION_OPERATION",
        "PAY_PERIOD", "PRICE_BASE", "SEX", "value", "Observation value"])
    mw = mw[mw["REF_AREA"].isin(ROSTER) & mw["period"].astype(str).isin([str(y) for y in YEARS])
            & mw["MEASURE"].eq("MR_WG_FT") & mw["UNIT_MEASURE"].eq("PT_WG_A_SAL_FT")
            & mw["AGGREGATION_OPERATION"].eq("MEDIAN") & mw["PAY_PERIOD"].eq("_Z")
            & mw["PRICE_BASE"].eq("_Z") & mw["SEX"].eq("_Z")].copy()
    mw["year"] = mw["period"].astype(int)
    if mw.duplicated(["REF_AREA", "year"]).any():
        raise ValueError("duplicate selected OECD key")
    ilo = pd.read_parquet(paths["youth_unemployment"], columns=[
        "country_iso3", "year", "indicator", "sex", "classif1", "source",
        "obs_status", "value", "obs_value"])
    ilo = ilo[ilo["country_iso3"].isin(ROSTER) & ilo["year"].isin(YEARS)
              & ilo["indicator"].eq("UNE_2EAP_SEX_AGE_RT") & ilo["sex"].eq("SEX_T")
              & ilo["classif1"].eq("AGE_YTHADULT_Y15-24")
              & ilo["source"].astype(str).str.startswith("XA:")].copy()
    if ilo.duplicated(["country_iso3", "year"]).any():
        raise ValueError("duplicate selected ILO key")
    gdp = pd.read_parquet(paths["real_gdp_growth"], columns=[
        "country_iso3", "year", "indicator_id", "value"])
    gdp = gdp[gdp["country_iso3"].isin(ROSTER) & gdp["year"].isin(YEARS)
              & gdp["indicator_id"].eq("NY.GDP.MKTP.KD.ZG")].copy()
    if gdp.duplicated(["country_iso3", "year"]).any():
        raise ValueError("duplicate selected WDI key")
    mw_rows = {(str(x.REF_AREA), int(x.year)): x for x in mw.itertuples(index=False)}
    ilo_rows = {(str(x.country_iso3), int(x.year)): x for x in ilo.itertuples(index=False)}
    gdp_rows = {(str(x.country_iso3), int(x.year)): x for x in gdp.itertuples(index=False)}
    rows = []
    for area in ROSTER:
        for year in YEARS:
            key = (area, year)
            o, i, g = mw_rows[key], ilo_rows[key], gdp_rows[key]
            mw_value = finite_or_none(o.value)
            # Named tuples sanitize the spaced OECD column; access the series by key.
            mw_original = finite_or_none(mw.loc[(mw["REF_AREA"] == area) & (mw["year"] == year), "Observation value"].iloc[0])
            ilo_value, ilo_original = finite_or_none(i.value), finite_or_none(i.obs_value)
            if (mw_value is None) != (mw_original is None) or (mw_value is not None and not math.isclose(mw_value, mw_original, rel_tol=0, abs_tol=1e-9)):
                raise ValueError(f"OECD normalized/source value mismatch: {key}")
            if (ilo_value is None) != (ilo_original is None) or (ilo_value is not None and not math.isclose(ilo_value, ilo_original, rel_tol=0, abs_tol=1e-9)):
                raise ValueError(f"ILO normalized/source value mismatch: {key}")
            rows.append({"country_iso3": area, "year": year,
                         MW_COL: mw_value, YOUTH_COL: ilo_value,
                         GDP_COL: finite_or_none(g.value),
                         "ilo_source": str(i.source),
                         "ilo_obs_status": None if pd.isna(i.obs_status) else str(i.obs_status)})
    return {
        "schema": "ieset-selected-upstream-slice-v1", "hypothesis_id": ID,
        "preregistration_commit": commit, "parent_manifest": {"path": MANIFEST_REL, "sha256": MANIFEST_SHA},
        "parents": SOURCE_FILES,
        "source_terms": {
            "oecd": "OECD MWUSD data; OECD standard permissions with attribution. Selected rows are a derived excerpt, not IESET-owned CC-BY content. Source: https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_EARNINGS@MIN2AVE,1.0/all?format=csvfilewithlabels (accessed 2026-05-05). OECD terms: https://www.oecd.org/en/about/terms-conditions.html",
            "ilostat": "ILO unemployment modelled estimates; CC-BY-4.0. Source: https://rplumber.ilo.org/data/indicator/?id=UNE_2EAP_SEX_AGE_RT_A&format=.csv (accessed 2026-05-05).",
            "world_bank_wdi": "World Bank WDI real GDP growth; CC-BY-4.0. Source: https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KD.ZG?format=json (accessed 2026-05-05).",
        },
        "selection": {"countries": list(ROSTER), "years": [YEARS[0], YEARS[-1]],
                      "oecd_aggregation": "MEDIAN", "ilo_sex": "SEX_T",
                      "ilo_age": "AGE_YTHADULT_Y15-24", "row_count": len(rows)},
        "rows": rows,
    }


def slice_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def slice_commit(prereg: str) -> str:
    current = (ROOT / SLICE_REL).read_bytes()
    if git_show("HEAD", SLICE_REL) != current:
        raise RuntimeError("commit selected source slice before estimation")
    commit = first_addition(SLICE_REL)
    if commit == prereg:
        raise RuntimeError("source slice must follow preregistration")
    parent = subprocess.run(["git", "merge-base", "--is-ancestor", prereg, commit], cwd=ROOT)
    if parent.returncode:
        raise RuntimeError("source slice does not descend from preregistration")
    if git_show(commit, SLICE_REL) != current:
        raise RuntimeError("selected source slice changed after first addition")
    listed = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if listed.returncode or listed.stdout.strip():
        raise RuntimeError("result existed in source-slice commit")
    return commit


def load_slice(prereg: str) -> tuple[dict[str, Any], str]:
    source_commit = slice_commit(prereg)
    saved = (ROOT / SLICE_REL).read_bytes()
    regenerated = slice_bytes(selected_slice(prereg))
    if saved != regenerated:
        raise ValueError("selected source slice differs from byte-exact raw-source replay")
    data = json.loads(saved)
    if data["selection"]["row_count"] != 160:
        raise ValueError("source slice row count differs from fixed key envelope")
    return data, source_commit


def model(data: dict[str, Any]) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf
    from scipy.stats import t as student_t
    panel = pd.DataFrame(data["rows"])
    keep = (panel[MW_COL].between(0, 100, inclusive="both")
            & panel[YOUTH_COL].between(0, 100, inclusive="both")
            & panel[GDP_COL].between(-100, 100, inclusive="both"))
    panel = panel[keep].copy()
    years = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[years >= MIN_YEARS].copy()
    panel["year"] = panel["year"].astype(int)
    n_countries = panel["country_iso3"].nunique()
    gate = {
        "fixed_source_keys": 160, "complete_case_observations": len(panel),
        "countries": int(n_countries),
        "min_years_per_retained_country": int(panel.groupby("country_iso3")["year"].size().min()) if len(panel) else 0,
        "year_counts": {str(k): int(v) for k, v in Counter(panel["year"]).items()},
        "source_status_counts": {str(k): int(v) for k, v in Counter(panel["ilo_obs_status"].fillna("blank")).items()},
        "eligible": len(panel) >= MIN_OBS and n_countries >= MIN_COUNTRIES,
    }
    if not gate["eligible"]:
        return gate, "INCONCLUSIVE", "frozen complete-case coverage gate failed", None
    formula = f"{YOUTH_COL} ~ {MW_COL} + {GDP_COL} + C(country_iso3) + C(year)"

    def fit(frame: "pd.DataFrame") -> dict[str, Any]:
        result = smf.ols(formula, data=frame).fit(
            cov_type="cluster", cov_kwds={"groups": frame["country_iso3"],
                                         "use_correction": True, "df_correction": True},
            use_t=True)
        if np.linalg.matrix_rank(result.model.exog) != result.model.exog.shape[1]:
            raise ValueError("rank-deficient fixed-effects design")
        beta, se = float(result.params[MW_COL]), float(result.bse[MW_COL])
        countries = int(frame["country_iso3"].nunique())
        if se <= 0 or not all(math.isfinite(x) for x in (beta, se, float(result.rsquared))):
            raise ValueError("nonfinite primary coefficient or uncertainty")
        df = countries - 1
        p = float(2 * student_t.sf(abs(beta / se), df))
        half = float(student_t.ppf(1 - P_MAX / 2, df) * se)
        if not all(math.isfinite(x) for x in (p, half)):
            raise ValueError("nonfinite clustered inference")
        return {"coefficient": beta, "std_error": se, "p_value": p,
                "ci_family": [beta - half, beta + half],
                "n_obs": int(len(frame)), "n_countries": countries,
                "r_squared": float(result.rsquared),
                "method": f"country/year FE OLS; country-clustered t({df}) inference"}

    sensitivity = panel[panel["year"].between(2021, 2024)].copy()
    gate["sensitivity_observations"] = int(len(sensitivity))
    gate["sensitivity_countries"] = int(sensitivity["country_iso3"].nunique())
    if len(sensitivity) < SENS_MIN_OBS or gate["sensitivity_countries"] < SENS_MIN_COUNTRIES:
        return gate, "INCONCLUSIVE", "frozen 2021-2024 sensitivity coverage gate failed", None
    try:
        primary = fit(panel)
        secondary = fit(sensitivity)
    except Exception as error:
        return gate, "INCONCLUSIVE", f"frozen estimator failed: {type(error).__name__}: {error}", None
    beta, p, s_beta = primary["coefficient"], primary["p_value"], secondary["coefficient"]
    if beta > 0 and p <= P_MAX and s_beta >= 0:
        verdict, reason = "SUPPORTED", "positive primary coefficient cleared family threshold and sensitivity sign"
    elif beta < 0 and p <= P_MAX and s_beta <= 0:
        verdict, reason = "REFUTED", "negative primary coefficient cleared family threshold and sensitivity sign"
    else:
        verdict, reason = "PARTIAL", "registered directional or sensitivity rule did not resolve the claim"
    return gate, verdict, reason, {"primary": primary, "sensitivity_2021_2024": secondary}


def artifacts(prereg: str, source_commit: str, gate: dict[str, Any], verdict: str,
              reason: str, result: dict[str, Any] | None, stamp: str) -> tuple[Any, ...]:
    inputs = [{"role": role, **pin} for role, pin in SOURCE_FILES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "causal_credit": 0, "policy_score_credit": 0}
    limits = [
        "The old 1990-2019 fit mixed OECD MEAN/MEDIAN and ILO sex/age rows; it does not validate this endpoint.",
        "The 2020-2024 interval is disjoint in time, but fitted old country identities were not saved and country independence is not claimed.",
        "The OECD selected dimension is MEDIAN although generic measure/unit labels say average wages.",
        "The ILO series is modelled; it may share macro inputs with the WDI control and is not independent survey validation.",
        "Same-year policy and unemployment can respond to each other; pandemic shocks and denominator movements remain.",
        "The five-slot family cutoff does not repair selection across the wider IESET archive.",
        "Youth-only descriptive association; no youth-versus-total, causal, school, welfare, or policy-score credit.",
    ]
    diagnostic = {
        "hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg, "source_slice_commit": source_commit,
        "template": "panel_fe", "preflight": gate, "estimate": result,
        "family_id": FAMILY_ID, "family_size": FAMILY_SIZE, "family_p_max": P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg, "source_slice_commit": source_commit,
        "status": verdict, "old_hypothesis_id": OLD_ID, "old_run_commit": OLD_COMMIT,
        "vintages": inputs, "selected_slice": {"path": SLICE_REL,
            "sha256": sha256(ROOT / SLICE_REL)}, "derived_panel": gate,
        "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "labour"},
        "preregistration": {"spec_commit": prereg, "steelman": STEELMAN_REL,
                            "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
                            "family_p_max": P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "selected_slice": manifest["selected_slice"],
                 "source_slice_commit": source_commit,
                 "outcome_measurement": "ILO modelled youth unemployment SEX_T AGE_YTHADULT_Y15-24"},
        "results": result, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration: {prereg}; selected source slice: {source_commit}.\n"
            f"Old quarantined run: {OLD_ID}, 246 observations in 18 countries, period ending 2019; exact fitted IDs not saved.\n"
            f"New 2020-2024 fit: {gate['complete_case_observations']} country-years, {gate['countries']} countries.\n"
            f"Only OECD MEDIAN aggregation and ILO SEX_T AGE_YTHADULT_Y15-24; family p cutoff {P_MAX}.\n")
    if result:
        primary = result["primary"]
        card += (f"Primary coefficient: {primary['coefficient']:+.6g} youth-unemployment percentage points "
                 f"per one ratio percentage point; clustered SE {primary['std_error']:.6g}; "
                 f"two-sided p={primary['p_value']:.6g}; family interval {primary['ci_family']}.\n"
                 f"Predeclared 2021-2024 sensitivity coefficient: "
                 f"{result['sensitivity_2021_2024']['coefficient']:+.6g}.\n")
    card += ("\nThe old run is not a youth-specific result. This is an ILO-modelled, "
             "same-year descriptive association and does not establish a minimum-wage "
             "employment effect. No youth-versus-total, causal, school, welfare, or policy-score credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "primary_coefficient": result["primary"]["coefficient"] if result else None,
             "primary_ci_family": result["primary"]["ci_family"] if result else None,
             "sensitivity_coefficient": result["sensitivity_2021_2024"]["coefficient"] if result else None,
             "family_p_max": P_MAX}
    rows = ([{"term": MW_COL, **result["primary"]}] if result else [])
    return diagnostic, manifest, packet, card, wrapper, chart, rows


def write_run(prereg: str, source_commit: str, gate: dict[str, Any], verdict: str,
              reason: str, result: dict[str, Any] | None) -> None:
    import pandas as pd
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = artifacts(prereg, source_commit, gate, verdict, reason, result, stamp)
    path = ROOT / RUN_REL
    path.mkdir(parents=True, exist_ok=False)
    (path / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (path / "diagnostics.json").write_text(json.dumps(expected[0], indent=2) + "\n", encoding="utf-8")
    (path / "manifest.yaml").write_text(yaml.safe_dump(expected[1], sort_keys=False), encoding="utf-8")
    (path / "evidence_packet.yaml").write_text(yaml.safe_dump(expected[2], sort_keys=False), encoding="utf-8")
    (path / "result_card.md").write_text(expected[3], encoding="utf-8")
    (path / "replication.py").write_text(expected[4], encoding="utf-8")
    (path / "chart_data.json").write_text(json.dumps(expected[5], indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(expected[6], columns=COEFFICIENT_COLUMNS).to_parquet(path / "coefficients.parquet", index=False)


def check_run(prereg: str, source_commit: str, source: dict[str, Any]) -> dict[str, Any]:
    import pandas as pd
    path = ROOT / RUN_REL
    diagnostic = json.loads((path / "diagnostics.json").read_text(encoding="utf-8"))
    if (path / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("saved hypothesis differs from preregistration")
    gate, verdict, reason, result = model(source)
    expected = artifacts(prereg, source_commit, gate, verdict, reason, result, diagnostic["run_utc"])
    actual = [diagnostic, yaml.safe_load((path / "manifest.yaml").read_text()),
              yaml.safe_load((path / "evidence_packet.yaml").read_text()),
              (path / "result_card.md").read_text(), (path / "replication.py").read_text(),
              json.loads((path / "chart_data.json").read_text())]
    for observed, registered in zip(actual, expected[:6]):
        if observed != registered:
            raise AssertionError("saved evidence differs from exact semantic replay")
    table = pd.read_parquet(path / "coefficients.parquet")
    if list(table.columns) != list(COEFFICIENT_COLUMNS) or len(table) != len(expected[6]):
        raise AssertionError("coefficient table shape differs from replay")
    for observed, registered in zip(table.to_dict(orient="records"), expected[6]):
        for key in COEFFICIENT_COLUMNS:
            if key == "ci_family":
                if any(not math.isclose(float(a), float(b), rel_tol=1e-8, abs_tol=1e-10)
                       for a, b in zip(observed[key], registered[key])):
                    raise AssertionError("family interval differs from replay")
            elif key in {"coefficient", "std_error", "p_value", "r_squared"}:
                if not math.isclose(float(observed[key]), float(registered[key]), rel_tol=1e-8, abs_tol=1e-10):
                    raise AssertionError(f"{key} differs from replay")
            elif observed[key] != registered[key]:
                raise AssertionError(f"{key} differs from replay")
    return {"hypothesis_id": ID, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--extract-slice", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = key_only_preflight()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1
    prereg = registration_commit()  # Must happen before any value or validity access.
    verify_spec()
    verify_sources()
    if args.extract_slice:
        if (ROOT / SLICE_REL).exists():
            raise FileExistsError(f"selected source slice already exists: {SLICE_REL}")
        content = slice_bytes(selected_slice(prereg))
        target = ROOT / SLICE_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        result = {"hypothesis_id": ID, "selected_slice": SLICE_REL,
                  "sha256": sha256(target), "bytes": len(content),
                  "fitted": False, "preregistration_commit": prereg}
    else:
        source, source_commit = load_slice(prereg)
        if args.check:
            result = check_run(prereg, source_commit, source)
        else:
            if (ROOT / RUN_REL).exists():
                raise FileExistsError(f"run already exists: {RUN_REL}")
            gate, verdict, reason, estimate = model(source)
            write_run(prereg, source_commit, gate, verdict, reason, estimate)
            result = {"hypothesis_id": ID, "verdict": verdict, "run_dir": RUN_REL}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
