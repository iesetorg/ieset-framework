#!/usr/bin/env python3
"""Promote and run Batch 07-09 welfare/labour/minimum-wage first wave.

This runner is intentionally scoped to Group 1 / Agent A4 ownership:
Batch 07 OECD SOCX, Batch 08 OECD EPL, and Batch 09 BLS minimum-wage
triage. It uses only local vintages already landed in the workspace.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
AUDITS = ROOT / "engine" / "audits"
HYPOTHESES = ROOT / "hypotheses"
STEELMEN = HYPOTHESES / "steelman"
OECD = ROOT / "data" / "vintages" / "oecd"
BLS = ROOT / "data" / "vintages" / "bls"
DERIVED = ROOT / "data" / "vintages" / "derived"
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"

COUNTRY_NAME_TO_ISO3 = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN",
    "Chile": "CHL", "Colombia": "COL", "Costa Rica*": "CRI",
    "Czech Republic": "CZE", "Denmark": "DNK", "Estonia": "EST",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Greece": "GRC",
    "Hungary": "HUN", "Iceland": "ISL", "Ireland": "IRL", "Israel": "ISR",
    "Italy": "ITA", "Japan": "JPN", "Korea": "KOR", "Latvia": "LVA",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Mexico": "MEX",
    "Netherlands": "NLD", "New Zealand": "NZL", "Norway": "NOR",
    "Poland": "POL", "Portugal": "PRT", "Slovak Republic": "SVK",
    "Slovenia": "SVN", "Spain": "ESP", "Sweden": "SWE",
    "Switzerland": "CHE", "Turkiye": "TUR", "Türkiye": "TUR",
    "United Kingdom": "GBR", "United States": "USA",
}

CASES = {
    "oecd_socx_public_social_spending_employment_tradeoff": {
        "batch": "07",
        "topic": "welfare",
        "claim": "Higher public social spending shares are associated with lower employment rates once country and year effects are absorbed.",
        "panel": "oecd",
        "outcome": "employment_rate",
        "treatment": "socx_public_gdp",
        "controls": ["gdp_growth"],
        "formula": "employment_rate ~ socx_public_gdp + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.08, "p_max": 0.10, "raw_diff_max": -0.5, "min_observations": 350, "min_units": 20},
        "outcome_dim": ["employment_labour"],
        "policy_family": ["welfare_state"],
    },
    "oecd_socx_open_economy_welfare_compatibility_panel": {
        "batch": "07",
        "topic": "welfare",
        "claim": "Open economies are more compatible with large public welfare states: social-spending employment penalties are smaller where trade exposure is high.",
        "panel": "oecd",
        "outcome": "employment_rate",
        "treatment": "socx_x_trade_open",
        "controls": ["socx_public_gdp", "trade_open_gdp", "gdp_growth"],
        "formula": "employment_rate ~ socx_x_trade_open + socx_public_gdp + trade_open_gdp + gdp_growth + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.002, "p_max": 0.10, "raw_diff_min": 0.2, "min_observations": 350, "min_units": 20},
        "outcome_dim": ["employment_labour", "trade_liberalisation"],
        "policy_family": ["welfare_state", "trade_policy"],
    },
    "oecd_epl_low_education_unemployment_panel_1985_2019": {
        "batch": "08",
        "topic": "labour",
        "claim": "Stricter OECD employment protection is associated with higher unemployment among below-upper-secondary adults.",
        "panel": "oecd",
        "outcome": "low_education_unemployment",
        "treatment": "epl",
        "controls": ["gdp_growth"],
        "formula": "low_education_unemployment ~ epl + gdp_growth + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.15, "p_max": 0.10, "raw_diff_min": 0.5, "min_observations": 350, "min_units": 20},
        "outcome_dim": ["employment_labour", "education"],
        "policy_family": ["labour_regulation"],
    },
    "oecd_low_education_unemployment_minimum_wage_bite": {
        "batch": "08",
        "topic": "labour",
        "claim": "Higher OECD statutory minimum-wage bite ratios are associated with higher low-education unemployment.",
        "panel": "oecd",
        "outcome": "low_education_unemployment",
        "treatment": "minimum_wage_bite",
        "controls": ["epl", "gdp_growth"],
        "formula": "low_education_unemployment ~ minimum_wage_bite + epl + gdp_growth + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.03, "p_max": 0.10, "raw_diff_min": 0.4, "min_observations": 250, "min_units": 15},
        "outcome_dim": ["employment_labour", "distribution"],
        "policy_family": ["labour_regulation", "minimum_wage"],
    },
    "oecd_activation_spending_low_education_unemployment": {
        "batch": "08",
        "topic": "labour",
        "claim": "Active labour-market programme spending is associated with lower low-education unemployment.",
        "panel": "oecd",
        "outcome": "low_education_unemployment",
        "treatment": "socx_active_gdp",
        "controls": ["epl", "gdp_growth"],
        "formula": "low_education_unemployment ~ socx_active_gdp + epl + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.25, "p_max": 0.10, "raw_diff_max": -0.4, "min_observations": 250, "min_units": 15},
        "outcome_dim": ["employment_labour", "education"],
        "policy_family": ["active_labour_market_policy"],
    },
    "oecd_epl_growth_shock_unemployment_persistence_panel": {
        "batch": "08",
        "topic": "labour",
        "claim": "Negative growth shocks translate into more persistent unemployment where employment protection is stricter.",
        "panel": "oecd",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "high_epl_x_negative_growth",
        "controls": ["epl", "negative_growth", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ high_epl_x_negative_growth + epl + negative_growth + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "raw_diff_min": 0.25, "min_observations": 350, "min_units": 20},
        "outcome_dim": ["employment_labour", "gdp_growth"],
        "policy_family": ["labour_regulation"],
    },
    "bls_qcew_county_food_service_minimum_wage_growth": {
        "batch": "09",
        "topic": "labour",
        "claim": "County food-service employment grows more slowly when the state minimum wage rises faster.",
        "panel": "county",
        "outcome": "food_emp_growth",
        "treatment": "min_wage_growth",
        "controls": ["total_emp_growth"],
        "formula": "food_emp_growth ~ min_wage_growth + total_emp_growth + C(unit) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.05, "p_max": 0.10, "raw_diff_max": -0.2, "min_observations": 20000, "min_units": 2000},
        "outcome_dim": ["employment_labour"],
        "policy_family": ["minimum_wage"],
    },
    "bls_qcew_state_food_service_minimum_wage_growth": {
        "batch": "09",
        "topic": "labour",
        "claim": "State food-service employment grows more slowly when the state minimum wage rises faster.",
        "panel": "state",
        "outcome": "food_emp_growth",
        "treatment": "min_wage_growth",
        "controls": ["total_emp_growth"],
        "formula": "food_emp_growth ~ min_wage_growth + total_emp_growth + C(unit) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.05, "p_max": 0.10, "raw_diff_max": -0.2, "min_observations": 350, "min_units": 45},
        "outcome_dim": ["employment_labour"],
        "policy_family": ["minimum_wage"],
    },
    "bls_oews_median_bite_food_service_employment_panel": {
        "batch": "09",
        "topic": "labour",
        "claim": "Higher state minimum-wage bite ratios relative to median wages are associated with weaker food-service employment growth.",
        "panel": "state",
        "outcome": "food_emp_growth",
        "treatment": "bite_ratio",
        "controls": ["total_emp_growth"],
        "formula": "food_emp_growth ~ bite_ratio + total_emp_growth + C(unit) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.10, "p_max": 0.10, "raw_diff_max": -0.2, "min_observations": 250, "min_units": 45},
        "outcome_dim": ["employment_labour"],
        "policy_family": ["minimum_wage"],
        "bite": "median",
    },
    "bls_minimum_wage_bite_low_tail_threshold_panel": {
        "batch": "09",
        "topic": "labour",
        "claim": "Very high minimum-wage bite ratios relative to the state low-wage tail predict weaker total employment growth.",
        "panel": "state",
        "outcome": "total_emp_growth",
        "treatment": "high_low_tail_bite",
        "controls": ["bite_ratio"],
        "formula": "total_emp_growth ~ high_low_tail_bite + bite_ratio + C(unit) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.2, "p_max": 0.10, "raw_diff_max": -0.2, "min_observations": 250, "min_units": 45},
        "outcome_dim": ["employment_labour"],
        "policy_family": ["minimum_wage"],
        "bite": "p10",
    },
}

TOPIC_MAP = {
    "welfare": "welfare_architecture",
    "labour": "labour",
}

OUTCOME_DIM_MAP = {
    "education": "employment_labour",
    "distribution": "poverty_inequality",
}

POLICY_FAMILY_MAP = {
    "welfare_state": "welfare_architecture",
    "labour_regulation": "labour_market",
    "minimum_wage": "labour_market",
    "active_labour_market_policy": "labour_market",
    "trade_policy": "trade_policy",
}

BLOCKERS = {
    "oecd_socx_unemployment_benefits_duration_panel": "SOCX aggregate vintage has unemployment compensation spending but no benefit-duration variable.",
    "oecd_socx_tax_wedge_employment_compatibility_panel": "No OECD tax-wedge vintage was found in local data/vintages/oecd.",
    "bls_qcew_county_food_service_wage_floor_border_design": "County adjacency/border-pair crosswalk is not landed locally.",
    "bls_oews_p10_bite_food_service_employment_panel": "Runnable, but displaced by the low-tail threshold total-employment screen to keep the requested wave to ten IDs.",
}


def latest(root: Path, pattern: str) -> Path:
    files = sorted(root.glob(pattern))
    if not files:
        raise FileNotFoundError(f"missing vintage {root}/{pattern}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_vintage(root: Path, pattern: str, manifest: dict, key: str, columns: list[str] | None = None) -> pd.DataFrame:
    path = latest(root, pattern)
    manifest[key] = {"vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    return pd.read_parquet(path, columns=columns)


def wdi_series(code: str, name: str, manifest: dict) -> pd.DataFrame:
    df = read_vintage(WDI, f"{code}@*.parquet", manifest, f"wdi:{code}")
    out = df[["country_iso3", "year", "value"]].rename(columns={"country_iso3": "country", "value": name}).copy()
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    return out.dropna(subset=["country", "year", name]).assign(year=lambda d: d["year"].astype(int))


def within_transform(d: pd.DataFrame, cols: list[str], unit_col: str) -> pd.DataFrame:
    out = d[cols + [unit_col, "year"]].copy()
    for col in cols:
        unit_mean = out.groupby(unit_col)[col].transform("mean")
        year_mean = out.groupby("year")[col].transform("mean")
        out[col] = out[col] - unit_mean - year_mean + out[col].mean()
    return out


def fixed_effect_fit(d: pd.DataFrame, outcome: str, regressors: list[str], cluster_col: str):
    transformed = within_transform(d, [outcome, *regressors], cluster_col)
    y = transformed[outcome]
    x = transformed[regressors]
    return sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": transformed[cluster_col]})


def build_oecd_panel() -> tuple[pd.DataFrame, dict]:
    manifest: dict = {}
    low = read_vintage(
        OECD,
        "DSD_LMS_low_education_unemployment_rate@*.parquet",
        manifest,
        "oecd:low_education_unemployment",
        ["REF_AREA", "SEX", "AGE", "ATTAINMENT_LEV", "period", "value"],
    )
    low = low[
        low["SEX"].eq("_T")
        & low["AGE"].eq("Y25T64")
        & low["ATTAINMENT_LEV"].eq("ISCED11A_0T2")
    ].copy()
    low["value"] = pd.to_numeric(low["value"], errors="coerce")
    low = (
        low.rename(columns={"REF_AREA": "country", "period": "year", "value": "low_education_unemployment"})
        .dropna(subset=["country", "year", "low_education_unemployment"])
        .assign(year=lambda d: pd.to_numeric(d["year"], errors="coerce").astype(int))
        .groupby(["country", "year"], as_index=False)["low_education_unemployment"]
        .mean()
    )

    epl = read_vintage(OECD, "OECD.ELS.EMP_DSD_EPL_OV_DF_EPL_OV_1.0@*.parquet", manifest, "oecd:epl")
    epl = epl[epl["indicator"].eq("EPR_V1")].copy()
    epl["country"] = epl["country"].map(COUNTRY_NAME_TO_ISO3)
    epl["epl"] = pd.to_numeric(epl["value"], errors="coerce")
    epl = epl[["country", "year", "epl"]].dropna()
    epl["year"] = epl["year"].astype(int)
    epl_p75 = epl.groupby("country")["epl"].quantile(0.75).rename("epl_p75")
    epl = epl.merge(epl_p75, on="country", how="left")
    epl["high_epl"] = (epl["epl"] >= epl["epl_p75"]).astype(int)

    mw = read_vintage(OECD, "MWUSD@*.parquet", manifest, "oecd:minimum_wage_bite")
    mw = mw[mw["MEASURE"].eq("MR_WG_FT")].copy()
    mw["minimum_wage_bite"] = pd.to_numeric(mw["value"], errors="coerce") / 100.0
    mw = mw.rename(columns={"REF_AREA": "country", "period": "year"})
    mw = mw[["country", "year", "minimum_wage_bite"]].dropna()
    mw["year"] = mw["year"].astype(int)

    socx = read_vintage(
        OECD,
        "DSD_SOCX_DF_SOCX_AGG@*.parquet",
        manifest,
        "oecd:socx",
        ["REF_AREA", "UNIT_MEASURE", "EXPEND_SOURCE", "SPENDING_TYPE", "PROGRAMME_TYPE", "period", "value"],
    )
    socx["value"] = pd.to_numeric(socx["value"], errors="coerce")
    base = socx[
        socx["UNIT_MEASURE"].eq("PT_B1GQ")
        & socx["EXPEND_SOURCE"].eq("ES10")
        & socx["SPENDING_TYPE"].eq("_T")
    ].rename(columns={"REF_AREA": "country", "period": "year"})
    total = (
        base[base["PROGRAMME_TYPE"].eq("_T")]
        .groupby(["country", "year"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "socx_public_gdp"})
    )
    active = (
        base[base["PROGRAMME_TYPE"].eq("TP60")]
        .groupby(["country", "year"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "socx_active_gdp"})
    )
    socx_panel = total.merge(active, on=["country", "year"], how="outer")
    socx_panel["year"] = socx_panel["year"].astype(int)

    panel = low.merge(epl[["country", "year", "epl", "high_epl"]], on=["country", "year"], how="outer")
    panel = panel.merge(mw, on=["country", "year"], how="outer")
    panel = panel.merge(socx_panel, on=["country", "year"], how="outer")
    for code, name in [
        ("NY.GDP.MKTP.KD.ZG", "gdp_growth"),
        ("SL.EMP.TOTL.SP.ZS", "employment_rate"),
        ("NE.TRD.GNFS.ZS", "trade_open_gdp"),
        ("SL.UEM.TOTL.ZS", "unemployment_rate"),
    ]:
        panel = panel.merge(wdi_series(code, name, manifest), on=["country", "year"], how="left")
    panel = panel.sort_values(["country", "year"])
    panel["socx_x_trade_open"] = panel["socx_public_gdp"] * panel["trade_open_gdp"]
    panel["negative_growth"] = (panel["gdp_growth"] < 0).astype(int)
    panel["high_epl_x_negative_growth"] = panel["high_epl"] * panel["negative_growth"]
    annual = panel[["country", "year", "unemployment_rate"]].dropna().drop_duplicates().sort_values(["country", "year"])
    annual["fwd_unemployment_change_2y"] = annual.groupby("country")["unemployment_rate"].shift(-2) - annual["unemployment_rate"]
    panel = panel.merge(annual[["country", "year", "fwd_unemployment_change_2y"]], on=["country", "year"], how="left")
    return panel, manifest


def min_wage_panel(manifest: dict) -> pd.DataFrame:
    mw = read_vintage(ROOT / "data" / "vintages" / "usdol", "state_minimum_wage_history@*.parquet", manifest, "usdol:state_minimum_wage")
    out = mw[["state_fips", "state_abbr", "year", "value"]].rename(columns={"value": "minimum_wage"}).copy()
    out["state_fips"] = out["state_fips"].astype(str).str.zfill(2)
    out["year"] = out["year"].astype(int)
    out["minimum_wage"] = pd.to_numeric(out["minimum_wage"], errors="coerce")
    out = out.dropna(subset=["minimum_wage"]).sort_values(["state_fips", "year"])
    out["min_wage_growth"] = 100 * (np.log(out["minimum_wage"]) - np.log(out.groupby("state_fips")["minimum_wage"].shift(1)))
    return out


def qcew_panel(level: str, manifest: dict) -> pd.DataFrame:
    if level == "county":
        food_pat = "QCEW_county_NAICS722_employment_panel@*.parquet"
        total_pat = "QCEW_county_total_employment_panel@*.parquet"
    else:
        food_pat = "QCEW_state_NAICS722_employment_panel@*.parquet"
        total_pat = "QCEW_state_total_employment_panel@*.parquet"
    food = read_vintage(BLS, food_pat, manifest, f"bls:{level}_food_service")
    total = read_vintage(BLS, total_pat, manifest, f"bls:{level}_total")
    f = food[["area_fips", "year", "annual_avg_emplvl"]].rename(columns={"area_fips": "unit", "annual_avg_emplvl": "food_emp"}).copy()
    t = total[["area_fips", "year", "annual_avg_emplvl"]].rename(columns={"area_fips": "unit", "annual_avg_emplvl": "total_emp"}).copy()
    for d in (f, t):
        d["unit"] = d["unit"].astype(str).str.zfill(5)
        d["year"] = d["year"].astype(int)
    panel = f.merge(t, on=["unit", "year"], how="inner")
    panel["state_fips"] = panel["unit"].str[:2]
    for col in ["food_emp", "total_emp"]:
        panel[col] = pd.to_numeric(panel[col], errors="coerce")
        panel[f"{col.replace('_emp', '')}_emp_growth"] = 100 * (
            np.log(panel[col]) - np.log(panel.sort_values(["unit", "year"]).groupby("unit")[col].shift(1))
        )
    panel = panel.merge(min_wage_panel(manifest), on=["state_fips", "year"], how="inner")
    return panel.replace([math.inf, -math.inf], np.nan)


def bite_panel(kind: str, manifest: dict) -> pd.DataFrame:
    pat = "minimum_wage_bite_ratio_state_panel@*.parquet" if kind == "median" else "minimum_wage_low_tail_bite_ratio_state_panel@*.parquet"
    key = f"derived:{kind}_minimum_wage_bite"
    df = read_vintage(DERIVED, pat, manifest, key)
    out = df[["state_fips", "year", "bite_ratio"]].copy()
    out["state_fips"] = out["state_fips"].astype(str).str.zfill(2)
    out["year"] = out["year"].astype(int)
    out["bite_ratio"] = pd.to_numeric(out["bite_ratio"], errors="coerce")
    p75 = out.groupby("state_fips")["bite_ratio"].quantile(0.75).rename("bite_p75")
    out = out.merge(p75, on="state_fips", how="left")
    out["high_low_tail_bite"] = (out["bite_ratio"] >= out["bite_p75"]).astype(int)
    return out


def build_bls_panel(kind: str, manifest: dict, bite_kind: str | None = None) -> pd.DataFrame:
    panel = qcew_panel(kind, manifest)
    if bite_kind:
        panel = panel.merge(bite_panel(bite_kind, manifest), on=["state_fips", "year"], how="inner")
    return panel


def verdict(cfg: dict, beta: float, p: float, raw_diff: float, n_obs: int, n_units: int) -> tuple[str, str]:
    gate = cfg["gate"]
    if n_obs < gate["min_observations"] or n_units < gate["min_units"]:
        return "INCONCLUSIVE_DATA_PENDING", "coverage is below the predeclared observation or unit gate"
    if cfg["direction"] == "positive":
        reg = beta >= gate["coef_min"] and p <= gate["p_max"]
        raw = raw_diff >= gate["raw_diff_min"]
    else:
        reg = beta <= gate["coef_max"] and p <= gate["p_max"]
        raw = raw_diff <= gate["raw_diff_max"]
    if reg and raw:
        return "SUPPORTED", "regression and raw high-low contrast both clear the predeclared gates"
    if reg or raw:
        return "PARTIAL", "one of the regression or raw high-low contrast gates clears"
    return "REFUTED", "neither the regression nor raw high-low contrast gate clears"


def fit_case(hid: str, cfg: dict, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    unit_col = "country" if cfg["panel"] == "oecd" else "unit"
    cols = [unit_col, "year", cfg["outcome"], cfg["treatment"], *cfg["controls"]]
    d = panel[cols].replace([math.inf, -math.inf], np.nan).dropna().copy()
    d["year"] = d["year"].astype(int)
    regressors = [cfg["treatment"], *cfg["controls"]]
    fit = fixed_effect_fit(d, cfg["outcome"], regressors, unit_col)
    term = cfg["treatment"]
    beta = float(fit.params[term])
    se = float(fit.bse[term])
    p = float(fit.pvalues[term])
    ci_low, ci_high = [float(x) for x in fit.conf_int().loc[term].tolist()]
    threshold = d[term].quantile(0.75)
    d["_high_treatment"] = (d[term] >= threshold).astype(int)
    means = d.groupby("_high_treatment")[cfg["outcome"]].mean().to_dict()
    raw_diff = float(means.get(1, np.nan) - means.get(0, np.nan))
    label, reason = verdict(cfg, beta, p, raw_diff, len(d), d[unit_col].nunique())
    return d, {
        "hypothesis_id": hid,
        "batch": cfg["batch"],
        "verdict_label": label,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_units": int(d[unit_col].nunique()),
        "unit_type": unit_col,
        "outcome": cfg["outcome"],
        "treatment": term,
        "coefficient": beta,
        "standard_error_cluster_unit": se,
        "p_value": p,
        "ci95": [ci_low, ci_high],
        "raw_top_quartile_minus_rest": raw_diff,
        "formula": cfg["formula"],
        "gate": cfg["gate"],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12.py",
    }


def write_hypothesis(hid: str, cfg: dict, d: pd.DataFrame) -> Path:
    topic = TOPIC_MAP.get(cfg["topic"], cfg["topic"])
    out_dir = HYPOTHESES / topic
    out_dir.mkdir(parents=True, exist_ok=True)
    unit_col = "country" if cfg["panel"] == "oecd" else "unit"
    countries = sorted(d["country"].dropna().astype(str).unique().tolist()) if unit_col == "country" else ["USA"]
    period = [int(d["year"].min()), int(d["year"].max())] if len(d) else [1985, 2025]
    outcome_dim = sorted({OUTCOME_DIM_MAP.get(dim, dim) for dim in cfg["outcome_dim"]})
    policy_family = sorted({POLICY_FAMILY_MAP.get(family, family) for family in cfg["policy_family"]})
    doc = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": cfg["claim"],
        "methodology_note": "Promoted for Batch 07-09 on 2026-05-12 using local OECD SOCX/EPL/minimum-wage and BLS/derived state or county vintages.",
        "evidence_type": "associational",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "panel",
            "exclusion_rules": ["drop rows missing outcome, treatment, or controls", "require local landed vintages only"],
        },
        "variables": {
            "outcome": [{"name": cfg["outcome"], "source": "local landed vintage", "transformation": "see runner"}],
            "treatment": [{"name": cfg["treatment"], "source": "local landed vintage", "transformation": "see runner"}],
            "controls": [{"name": c, "source": "local landed vintage", "transformation": "level or growth"} for c in cfg["controls"]],
        },
        "estimator": {"template": "panel_fe", "fixed_effects": [unit_col, "year"], "clustering": unit_col},
        "falsification": {
            "rule": f"Supported only if `{cfg['treatment']}` clears coefficient and raw contrast gates.",
            "test": f"panel_fe_{hid}",
            "threshold": json.dumps(cfg["gate"], sort_keys=True),
        },
        "prior_confidence": 0.56,
        "disclosure": "Screening panel estimate for readiness and first-run triage; not a structural causal claim.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": period,
            "countries": ["OECD"] if unit_col == "country" else ["USA"],
            "outcome_dim": outcome_dim,
            "policy_family": policy_family,
            "treatment_tags": [cfg["treatment"]],
        },
        "notes": f"Generated by A4 Batch 07-09 runner; reproducible via engine/runs/{hid}/replication.py.",
    }
    path = out_dir / f"{hid}.yaml"
    path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(doc, sort_keys=False, allow_unicode=False))
    STEELMEN.mkdir(parents=True, exist_ok=True)
    (STEELMEN / f"{hid}.md").write_text(
        f"# Steelman - {hid}\n\n"
        f"The strongest version of the claim is: {cfg['claim']}\n\n"
        "The skeptical case is that these first-run panels may still mix policy effects with omitted institutions, sector composition, "
        "macro shocks, and measurement differences. A fair reading treats this as a readiness screen with fixed effects and transparent gates.\n"
    )
    return path


def write_run(hid: str, cfg: dict, d: pd.DataFrame, diag: dict, manifest: dict) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    pd.DataFrame([{
        "hypothesis_id": hid,
        "term": cfg["treatment"],
        "estimate": diag["coefficient"],
        "std_error": diag["standard_error_cluster_unit"],
        "p_value": diag["p_value"],
        "ci95_low": diag["ci95"][0],
        "ci95_high": diag["ci95"][1],
        "n_observations": diag["n_observations"],
        "n_units": diag["n_units"],
    }]).to_parquet(out_dir / "coefficients.parquet", index=False)
    chart = d.groupby(["year", "_high_treatment"], as_index=False)[cfg["outcome"]].mean().rename(columns={cfg["outcome"]: "mean_outcome"})
    (out_dir / "chart_data.json").write_text(json.dumps({"series": chart.to_dict("records")}, indent=2) + "\n")
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": diag["run_utc"],
        "verdict_label": diag["verdict_label"],
        "runner": diag["runner"],
        "formula": cfg["formula"],
        "vintages": manifest,
    }, sort_keys=False))
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import subprocess, sys\n\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12.py'), '{hid}']))\n"
    )
    (out_dir / "replication.py").write_text(wrapper)
    (out_dir / "result_card.md").write_text(f"""# Result card - {hid}

**Verdict:** {diag['verdict_label']} - {diag['verdict_reason']}.

## Plain-English Claim

{cfg['claim']}

## Results

- Usable panel: **{diag['n_observations']:,} observations**, **{diag['n_units']:,} {diag['unit_type']} units**.
- Treatment: `{cfg['treatment']}`.
- Outcome: `{cfg['outcome']}`.
- Coefficient: **{diag['coefficient']:.4f}** (clustered SE {diag['standard_error_cluster_unit']:.4f}, p={diag['p_value']:.4f}).
- Top-quartile raw contrast: **{diag['raw_top_quartile_minus_rest']:.4f}**.

## Specification

`{cfg['formula']}`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
""")
    evidence = {
        "hypothesis_id": hid,
        "claim": cfg["claim"],
        "verdict": diag["verdict_label"],
        "diagnostics": "diagnostics.json",
        "result_card": "result_card.md",
        "manifest": "manifest.yaml",
    }
    (out_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(evidence, sort_keys=False))


def run_one(hid: str) -> dict:
    cfg = CASES[hid]
    if cfg["panel"] == "oecd":
        panel, manifest = build_oecd_panel()
    elif cfg["panel"] == "county":
        manifest = {}
        panel = build_bls_panel("county", manifest)
    else:
        manifest = {}
        panel = build_bls_panel("state", manifest, cfg.get("bite"))
    d, diag = fit_case(hid, cfg, panel)
    write_hypothesis(hid, cfg, d)
    write_run(hid, cfg, d, diag, manifest)
    return diag


def write_audit(results: list[dict], readiness: list[dict]) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    out = AUDITS / f"welfare_labour_minwage_batches_07_09_a4_results_{ts}.md"
    by_batch = {}
    for row in results:
        by_batch[row["batch"]] = by_batch.get(row["batch"], 0) + 1
    lines = [
        "# Batch 07-09 A4 welfare/labour/minimum-wage first-run audit",
        "",
        f"Run UTC: {ts}",
        "",
        "## Tally",
        "",
        f"- Selected immediately runnable IDs: {len(CASES)}",
        f"- Successfully run IDs: {len(results)}",
        f"- Batch 07 run count: {by_batch.get('07', 0)}",
        f"- Batch 08 run count: {by_batch.get('08', 0)}",
        f"- Batch 09 run count: {by_batch.get('09', 0)}",
        f"- Blocked or deferred IDs noted: {len(readiness)}",
        "",
        "## Results",
        "",
        "| Rank | Hypothesis id | Batch | Verdict | N | Units | Coef | p |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(results, 1):
        lines.append(
            f"| {i} | `{row['hypothesis_id']}` | {row['batch']} | {row['verdict_label']} | "
            f"{row['n_observations']} | {row['n_units']} | {row['coefficient']:.4f} | {row['p_value']:.4f} |"
        )
    lines += ["", "## Blockers And Deferred", ""]
    for item in readiness:
        lines.append(f"- `{item['hypothesis_id']}`: {item['blocker']}")
    lines += ["", "## Changed Run Paths", ""]
    for row in results:
        lines.append(f"- `engine/runs/{row['hypothesis_id']}/`")
    out.write_text("\n".join(lines) + "\n")
    return out


def main(argv: list[str]) -> int:
    targets = argv[1:] or list(CASES)
    results = []
    for hid in targets:
        if hid not in CASES:
            raise KeyError(hid)
        diag = run_one(hid)
        results.append(diag)
        print(f"{hid}: {diag['verdict_label']} n={diag['n_observations']} units={diag['n_units']} coef={diag['coefficient']:.4f} p={diag['p_value']:.4f}")
    readiness = [{"hypothesis_id": hid, "blocker": blocker} for hid, blocker in BLOCKERS.items()]
    audit = write_audit(results, readiness)
    json_audit = audit.with_suffix(".json")
    json_audit.write_text(json.dumps({"results": results, "blockers": readiness}, indent=2) + "\n")
    print(f"audit: {audit.relative_to(ROOT)}")
    print(f"audit_json: {json_audit.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
