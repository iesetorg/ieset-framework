#!/usr/bin/env python3
"""Generate Worker C BIS/OECD/WGI first-tranche panel verdicts.

The script uses only pinned vintages already present on disk. It writes new
hypothesis YAML, steelmen, per-run replication wrappers, and run artifacts.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
BIS = ROOT / "data" / "vintages" / "bis"
OECD = ROOT / "data" / "vintages" / "oecd"
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"
WGI = ROOT / "data" / "vintages" / "wgi"

OECD_SAMPLE = [
    "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST",
    "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN",
    "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT",
    "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA",
]

BIS_ISO2_TO_ISO3 = {
    "AU": "AUS", "AT": "AUT", "BE": "BEL", "BR": "BRA", "CA": "CAN",
    "CH": "CHE", "CL": "CHL", "CN": "CHN", "CO": "COL", "CZ": "CZE",
    "DE": "DEU", "DK": "DNK", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "GB": "GBR", "GR": "GRC", "HK": "HKG", "HU": "HUN", "ID": "IDN",
    "IE": "IRL", "IL": "ISR", "IN": "IND", "IT": "ITA", "JP": "JPN",
    "KR": "KOR", "LU": "LUX", "MX": "MEX", "MY": "MYS", "NL": "NLD",
    "NO": "NOR", "NZ": "NZL", "PL": "POL", "PT": "PRT", "RU": "RUS",
    "SA": "SAU", "SE": "SWE", "SG": "SGP", "TH": "THA", "TR": "TUR",
    "US": "USA", "ZA": "ZAF",
}

WGI_SAMPLE = [
    "ALB", "ARG", "AUS", "AUT", "BEL", "BGD", "BRA", "CAN", "CHE", "CHL",
    "CHN", "COL", "CZE", "DEU", "DNK", "EGY", "ESP", "EST", "ETH", "FIN",
    "FRA", "GBR", "GHA", "GRC", "HUN", "IDN", "IND", "IRL", "ISR", "ITA",
    "JPN", "KAZ", "KEN", "KOR", "LTU", "LVA", "MAR", "MEX", "MYS", "NGA",
    "NLD", "NOR", "NZL", "PAK", "PER", "PHL", "POL", "PRT", "ROU", "RUS",
    "SGP", "SVK", "SVN", "SWE", "THA", "TUR", "UKR", "USA", "VNM", "ZAF",
]


def latest(root: Path, stem: str) -> Path:
    files = sorted(root.glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage: {root}/{stem}@*.parquet")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def qnum(period: str) -> int:
    year, q = str(period).split("-Q")
    return int(year) * 4 + int(q)


def qyear(q: int) -> int:
    return q // 4


def bis_quarterly(df: pd.DataFrame, country_col: str, value_col: str = "value") -> pd.DataFrame:
    out = df[[country_col, "period", value_col]].rename(columns={country_col: "bis_country", value_col: "value"}).copy()
    out["q"] = out["period"].map(qnum)
    out["year"] = out["q"].map(qyear)
    out["country"] = out["bis_country"].map(BIS_ISO2_TO_ISO3)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["country", "q", "value"])


def wdi_series(stem: str, name: str) -> tuple[pd.DataFrame, dict]:
    path = latest(WDI, stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].rename(columns={"country_iso3": "country", "value": name}).copy()
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out[out["country"].astype(str).str.fullmatch(r"[A-Z]{3}")]
    out = out.dropna(subset=[name])
    return out, {
        "publisher": "world_bank_wdi",
        "series": stem,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def add_forward_log_growth(df: pd.DataFrame, value_col: str, horizons: list[int], prefix: str) -> pd.DataFrame:
    out = df.sort_values(["country", "q"]).copy()
    for h in horizons:
        future = out.groupby("country")[value_col].shift(-h)
        past = out.groupby("country")[value_col].shift(h)
        out[f"fwd_{prefix}_growth_{h}q"] = 100 * (np.log(future) - np.log(out[value_col]))
        out[f"lag_{prefix}_growth_{h}q"] = 100 * (np.log(out[value_col]) - np.log(past))
    return out


def bis_panel() -> tuple[pd.DataFrame, dict]:
    paths = {
        "WS_CBPOL": latest(BIS, "WS_CBPOL"),
        "WS_CREDIT_GAP": latest(BIS, "WS_CREDIT_GAP"),
        "WS_DSR": latest(BIS, "WS_DSR"),
        "WS_SPP": latest(BIS, "WS_SPP"),
    }
    credit_raw = pd.read_parquet(paths["WS_CREDIT_GAP"])
    gap = bis_quarterly(credit_raw[credit_raw["CG_DTYPE"].eq("C")], "BORROWERS_CTY").rename(columns={"value": "credit_gap"})
    gap = gap.sort_values(["country", "q"])
    gap["fwd_credit_gap_change_8q"] = gap.groupby("country")["credit_gap"].shift(-8) - gap["credit_gap"]

    dsr_raw = pd.read_parquet(paths["WS_DSR"])
    dsr = bis_quarterly(dsr_raw[dsr_raw["DSR_BORROWERS"].eq("H")], "BORROWERS_CTY").rename(columns={"value": "household_dsr"})
    p75 = dsr.groupby("country")["household_dsr"].quantile(0.75).rename("dsr_p75")
    dsr = dsr.merge(p75, on="country", how="left")
    dsr["high_household_dsr"] = ((dsr["household_dsr"] >= 12.0) & (dsr["household_dsr"] >= dsr["dsr_p75"])).astype(int)

    spp_raw = pd.read_parquet(paths["WS_SPP"])
    house = bis_quarterly(spp_raw[spp_raw["VALUE"].eq("R")], "REF_AREA").rename(columns={"value": "real_house_price"})
    house = add_forward_log_growth(house, "real_house_price", [8], "real_house_price")

    pol_raw = pd.read_parquet(paths["WS_CBPOL"])
    pol_m = pol_raw[pol_raw["FREQ"].eq("M")][["REF_AREA", "period", "value"]].copy()
    pol_m["date"] = pd.to_datetime(pol_m["period"] + "-01", errors="coerce")
    pol_m["q"] = pol_m["date"].dt.year * 4 + ((pol_m["date"].dt.month - 1) // 3 + 1)
    pol_m["country"] = pol_m["REF_AREA"].map(BIS_ISO2_TO_ISO3)
    pol_m["policy_rate"] = pd.to_numeric(pol_m["value"], errors="coerce")
    policy = pol_m.dropna(subset=["country", "q", "policy_rate"]).groupby(["country", "q"], as_index=False)["policy_rate"].mean()
    policy["year"] = policy["q"].map(qyear)
    policy = policy.sort_values(["country", "q"])
    policy["policy_rate_change_4q"] = policy["policy_rate"] - policy.groupby("country")["policy_rate"].shift(4)
    policy["policy_tightening_2pp"] = (policy["policy_rate_change_4q"] >= 2.0).astype(int)

    panel = dsr[["country", "q", "year", "household_dsr", "high_household_dsr"]]
    panel = panel.merge(gap[["country", "q", "year", "credit_gap", "fwd_credit_gap_change_8q"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(house[["country", "q", "year", "real_house_price", "fwd_real_house_price_growth_8q", "lag_real_house_price_growth_8q"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(policy[["country", "q", "year", "policy_rate", "policy_rate_change_4q", "policy_tightening_2pp"]], on=["country", "q", "year"], how="outer")

    u, umeta = wdi_series("SL.UEM.TOTL.ZS", "unemployment_rate")
    c, cmeta = wdi_series("NE.CON.PRVT.KD.ZG", "consumption_growth")
    panel = panel.merge(u, on=["country", "year"], how="left")
    panel = panel.merge(c, on=["country", "year"], how="left")
    annual = panel[["country", "year", "unemployment_rate", "consumption_growth"]].drop_duplicates().sort_values(["country", "year"])
    annual["fwd_unemployment_change_2y"] = annual.groupby("country")["unemployment_rate"].shift(-2) - annual["unemployment_rate"]
    annual["fwd_consumption_growth_2y_avg"] = (
        annual.groupby("country")["consumption_growth"].shift(-1) + annual.groupby("country")["consumption_growth"].shift(-2)
    ) / 2
    panel = panel.merge(annual[["country", "year", "fwd_unemployment_change_2y", "fwd_consumption_growth_2y_avg"]], on=["country", "year"], how="left")

    manifest = {
        name: {"publisher": "bis", "series": name, "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        for name, path in paths.items()
    }
    manifest["SL.UEM.TOTL.ZS"] = umeta
    manifest["NE.CON.PRVT.KD.ZG"] = cmeta
    return panel, manifest


BIS_CONFIGS = {
    "bis_household_dsr_unemployment_surge_panel": {
        "topic": "labour",
        "title": "Household debt-service stress predicts unemployment surge",
        "claim": "In BIS/WDI country panels, high household debt-service stress is followed by larger unemployment increases over the next two years.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "controls": ["unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ high_household_dsr + household_dsr + unemployment_rate + C(country) + C(year)",
        "gate": {"coef_min": 0.50, "p_max": 0.05, "mean_diff_min": 0.50, "min_countries": 15, "min_observations": 400},
        "threshold_text": "High DSR is BIS household DSR >= 12 percent and >= country p75; outcome is WDI unemployment-rate change from year t to t+2.",
        "prior": 0.55,
    },
    "bis_household_dsr_consumption_slowdown_panel": {
        "topic": "monetary",
        "title": "Household debt-service stress predicts consumption slowdown",
        "claim": "In BIS/WDI country panels, high household debt-service stress is followed by weaker private-consumption growth over the next two years.",
        "outcome": "fwd_consumption_growth_2y_avg",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "controls": ["consumption_growth"],
        "formula": "fwd_consumption_growth_2y_avg ~ high_household_dsr + household_dsr + consumption_growth + C(country) + C(year)",
        "gate": {"coef_max": -1.00, "p_max": 0.05, "mean_diff_max": -1.00, "min_countries": 15, "min_observations": 400},
        "threshold_text": "High DSR is BIS household DSR >= 12 percent and >= country p75; outcome is the average WDI real private-consumption growth rate in years t+1 and t+2.",
        "prior": 0.60,
    },
    "bis_policy_rate_house_price_cooling_panel": {
        "topic": "housing",
        "title": "Policy-rate tightening predicts house-price cooling",
        "claim": "In BIS panels, policy-rate tightening episodes are followed by materially weaker real house-price growth over the next eight quarters.",
        "outcome": "fwd_real_house_price_growth_8q",
        "treatment": "policy_tightening_2pp",
        "continuous": "policy_rate_change_4q",
        "controls": ["lag_real_house_price_growth_8q"],
        "formula": "fwd_real_house_price_growth_8q ~ policy_tightening_2pp + policy_rate_change_4q + lag_real_house_price_growth_8q + C(country) + C(year)",
        "gate": {"coef_max": -2.00, "p_max": 0.05, "mean_diff_max": -2.00, "min_countries": 20, "min_observations": 700},
        "threshold_text": "Policy tightening is a >= 2 pp rise in BIS central-bank policy rates over four quarters; outcome is 8-quarter forward real residential property-price log growth.",
        "prior": 0.62,
    },
    "bis_policy_rate_credit_gap_compression_panel": {
        "topic": "monetary",
        "title": "Policy-rate tightening predicts credit-gap compression",
        "claim": "In BIS panels, policy-rate tightening episodes are followed by compression in the BIS credit-to-GDP gap over the next eight quarters.",
        "outcome": "fwd_credit_gap_change_8q",
        "treatment": "policy_tightening_2pp",
        "continuous": "policy_rate_change_4q",
        "controls": ["credit_gap"],
        "formula": "fwd_credit_gap_change_8q ~ policy_tightening_2pp + policy_rate_change_4q + credit_gap + C(country) + C(year)",
        "gate": {"coef_max": -1.50, "p_max": 0.05, "mean_diff_max": -1.50, "min_countries": 20, "min_observations": 700},
        "threshold_text": "Policy tightening is a >= 2 pp rise in BIS central-bank policy rates over four quarters; outcome is credit-gap change from t to t+8 quarters.",
        "prior": 0.58,
    },
}


def fit_gate(panel: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    cols = ["country", "year", cfg["outcome"], cfg["treatment"], cfg["continuous"]] + cfg["controls"]
    d = panel[cols].replace([math.inf, -math.inf], np.nan).dropna().copy()
    d["year"] = d["year"].astype(int)
    fit = smf.ols(cfg["formula"], data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    term = cfg["treatment"]
    beta = float(fit.params[term])
    se = float(fit.bse[term])
    p = float(fit.pvalues[term])
    ci_low, ci_high = [float(x) for x in fit.conf_int().loc[term].tolist()]
    group = d.groupby(term)[cfg["outcome"]].agg(["mean", "count"]).to_dict("index")
    base = float(group.get(0, {}).get("mean", np.nan))
    high = float(group.get(1, {}).get("mean", np.nan))
    diff = high - base
    gate = cfg["gate"]
    enough = len(d) >= gate["min_observations"] and d["country"].nunique() >= gate["min_countries"]
    if not enough:
        verdict, detail = "inconclusive", "insufficient coverage for the predeclared gate"
    elif "coef_min" in gate:
        effect = beta >= gate["coef_min"] and p <= gate["p_max"]
        raw = diff >= gate["mean_diff_min"]
        verdict, detail = verdict_from(effect, raw)
    else:
        effect = beta <= gate["coef_max"] and p <= gate["p_max"]
        raw = diff <= gate["mean_diff_max"]
        verdict, detail = verdict_from(effect, raw)
    return d, {
        "verdict": verdict,
        "verdict_detail": detail,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "coefficient": beta,
        "standard_error_cluster_country": se,
        "p_value": p,
        "ci95": [ci_low, ci_high],
        "raw_high_minus_normal_mean": diff,
        "normal_mean": base,
        "high_mean": high,
        "high_count": int(group.get(1, {}).get("count", 0)),
    }


def verdict_from(effect: bool, raw: bool) -> tuple[str, str]:
    if effect and raw:
        return "supported", "regression and raw contrast both clear the predeclared gates"
    if effect or raw:
        return "partial", "one of the regression or raw-contrast gates clears, but not both"
    return "refuted", "neither the regression nor raw-contrast gate clears"


def oecd_idd_series(measure: str, name: str, poverty_line: str | None = None) -> tuple[pd.DataFrame, dict]:
    stem = "OECD.WISE.INE_DSD_IDD_DF_IDD_1.0"
    path = latest(OECD, stem)
    df = pd.read_parquet(path)
    d = df[(df["MEASURE"].eq(measure)) & (df["AGE"].eq("_T")) & (df["DEFINITION"].eq("D_CUR"))].copy()
    if poverty_line is not None:
        d = d[d["POVERTY_LINE"].eq(poverty_line)]
    out = d[["REF_AREA", "period", "value"]].rename(columns={"REF_AREA": "country", "value": name}).copy()
    out["year"] = out["period"].astype(str).str[:4].astype(int)
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out[out["country"].isin(OECD_SAMPLE)].dropna(subset=[name])
    out = out[["country", "year", name]].groupby(["country", "year"], as_index=False).mean()
    return out, {"publisher": "oecd", "series": stem, "filters": {"MEASURE": measure, "AGE": "_T", "DEFINITION": "D_CUR", "POVERTY_LINE": poverty_line or "_Z"}, "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}


OECD_CONFIGS = {
    "oecd_market_to_disposable_gini_compression_panel": {
        "topic": "distribution",
        "title": "OECD tax-transfer systems compress market-income Gini",
        "claim": "Across OECD country-years, disposable-income Gini is materially lower than market-income Gini after taxes and transfers.",
        "outcome": "gini_compression",
        "threshold_text": "Supported if mean market-minus-disposable Gini compression is >= 0.08 and at least 90 percent of country-years are positive, with at least 300 observations and 25 countries.",
        "gate": {"mean_min": 0.08, "share_min": 0.90, "min_observations": 300, "min_countries": 25},
        "prior": 0.90,
    },
    "oecd_public_transfers_poverty_reduction_panel": {
        "topic": "distribution",
        "title": "OECD taxes and transfers reduce relative poverty",
        "claim": "Across OECD country-years, disposable-income poverty rates are materially lower than market-income poverty rates at the 50 percent median-income line.",
        "outcome": "poverty_reduction",
        "threshold_text": "Supported if mean market-minus-disposable poverty reduction is >= 5 percentage points and at least 85 percent of country-years are positive, with at least 300 observations and 25 countries.",
        "gate": {"mean_min": 5.0, "share_min": 0.85, "min_observations": 300, "min_countries": 25},
        "prior": 0.88,
    },
}


def oecd_panel(hid: str) -> tuple[pd.DataFrame, dict]:
    if hid == "oecd_market_to_disposable_gini_compression_panel":
        market, mmeta = oecd_idd_series("INC_MRKT_GINI", "market_gini")
        disp, dmeta = oecd_idd_series("INC_DISP_GINI", "disposable_gini")
        panel = market.merge(disp, on=["country", "year"], how="inner")
        panel["gini_compression"] = panel["market_gini"] - panel["disposable_gini"]
        return panel, {"market_gini": mmeta, "disposable_gini": dmeta}
    market, mmeta = oecd_idd_series("PR_INC_MRKT", "market_poverty", "PL_50")
    disp, dmeta = oecd_idd_series("PR_INC_DISP", "disposable_poverty", "PL_50")
    panel = market.merge(disp, on=["country", "year"], how="inner")
    panel["poverty_reduction"] = panel["market_poverty"] - panel["disposable_poverty"]
    return panel, {"market_poverty": mmeta, "disposable_poverty": dmeta}


def descriptive_verdict(panel: pd.DataFrame, cfg: dict) -> dict:
    d = panel[["country", "year", cfg["outcome"]]].dropna()
    mean = float(d[cfg["outcome"]].mean())
    share = float((d[cfg["outcome"]] > 0).mean())
    gate = cfg["gate"]
    enough = len(d) >= gate["min_observations"] and d["country"].nunique() >= gate["min_countries"]
    if not enough:
        verdict, detail = "inconclusive", "insufficient coverage for the predeclared gate"
    elif mean >= gate["mean_min"] and share >= gate["share_min"]:
        verdict, detail = "supported", "mean magnitude and positive-share gates both clear"
    elif mean >= gate["mean_min"] or share >= gate["share_min"]:
        verdict, detail = "partial", "one of the mean magnitude or positive-share gates clears"
    else:
        verdict, detail = "refuted", "neither the mean magnitude nor positive-share gate clears"
    return {
        "verdict": verdict,
        "verdict_detail": detail,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "mean_effect": mean,
        "share_positive": share,
        "country_mean_min": float(d.groupby("country")[cfg["outcome"]].mean().min()),
        "country_mean_max": float(d.groupby("country")[cfg["outcome"]].mean().max()),
    }


WGI_CONFIG = {
    "wgi_regulatory_quality_fdi_growth_panel": {
        "topic": "institutional_quality",
        "title": "Regulatory quality predicts subsequent FDI intensity",
        "claim": "Across country-years, higher WGI Regulatory Quality predicts higher average FDI net inflows as a share of GDP over the next three years after fixed effects and macro controls.",
        "outcome": "fwd_fdi_gdp_3y_avg",
        "treatment": "regulatory_quality",
        "controls": ["fdi_gdp", "gdp_growth", "trade_share"],
        "formula": "fwd_fdi_gdp_3y_avg ~ regulatory_quality + fdi_gdp + gdp_growth + trade_share + C(country) + C(year)",
        "threshold_text": "Supported if beta(regulatory_quality) >= 0.25 pp of GDP with p <= 0.10, and the top-minus-bottom RQ-tercile raw mean difference is >= 1.0 pp of GDP, with at least 800 observations and 40 countries.",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "raw_min": 1.0, "min_observations": 800, "min_countries": 40},
        "prior": 0.57,
    }
}


def wgi_panel() -> tuple[pd.DataFrame, dict]:
    rq_path = latest(WGI, "GOV_WGI_RQ.EST")
    rq = pd.read_parquet(rq_path)[["country_iso3", "year", "value"]].rename(columns={"country_iso3": "country", "value": "regulatory_quality"})
    rq["regulatory_quality"] = pd.to_numeric(rq["regulatory_quality"], errors="coerce")
    rq = rq[rq["country"].isin(WGI_SAMPLE)].dropna()
    fdi, fdi_meta = wdi_series("BX.KLT.DINV.WD.GD.ZS", "fdi_gdp")
    growth, growth_meta = wdi_series("NY.GDP.MKTP.KD.ZG", "gdp_growth")
    trade, trade_meta = wdi_series("NE.TRD.GNFS.ZS", "trade_share")
    panel = rq.merge(fdi, on=["country", "year"], how="inner").merge(growth, on=["country", "year"], how="inner").merge(trade, on=["country", "year"], how="inner")
    panel = panel.sort_values(["country", "year"])
    panel["fwd_fdi_gdp_3y_avg"] = (
        panel.groupby("country")["fdi_gdp"].shift(-1) +
        panel.groupby("country")["fdi_gdp"].shift(-2) +
        panel.groupby("country")["fdi_gdp"].shift(-3)
    ) / 3
    return panel, {
        "regulatory_quality": {"publisher": "wgi", "series": "GOV_WGI_RQ.EST", "vintage_file": str(rq_path.relative_to(ROOT)), "sha256": sha256(rq_path)},
        "fdi_gdp": fdi_meta,
        "gdp_growth": growth_meta,
        "trade_share": trade_meta,
    }


def wgi_verdict(panel: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    cols = ["country", "year", cfg["outcome"], cfg["treatment"]] + cfg["controls"]
    d = panel[cols].replace([math.inf, -math.inf], np.nan).dropna().copy()
    d["year"] = d["year"].astype(int)
    d["rq_tercile"] = pd.qcut(d["regulatory_quality"], 3, labels=False, duplicates="drop")
    fit = smf.ols(cfg["formula"], data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    beta = float(fit.params[cfg["treatment"]])
    se = float(fit.bse[cfg["treatment"]])
    p = float(fit.pvalues[cfg["treatment"]])
    lo, hi = [float(x) for x in fit.conf_int().loc[cfg["treatment"]].tolist()]
    raw = float(d.loc[d["rq_tercile"].eq(2), cfg["outcome"]].mean() - d.loc[d["rq_tercile"].eq(0), cfg["outcome"]].mean())
    gate = cfg["gate"]
    enough = len(d) >= gate["min_observations"] and d["country"].nunique() >= gate["min_countries"]
    if not enough:
        verdict, detail = "inconclusive", "insufficient coverage for the predeclared gate"
    else:
        verdict, detail = verdict_from(beta >= gate["coef_min"] and p <= gate["p_max"], raw >= gate["raw_min"])
    return d, {
        "verdict": verdict,
        "verdict_detail": detail,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "coefficient": beta,
        "standard_error_cluster_country": se,
        "p_value": p,
        "ci95": [lo, hi],
        "raw_top_minus_bottom_tercile_mean": raw,
    }


def write_yaml(hid: str, cfg: dict, countries: list[str], period: list[int], kind: str) -> None:
    topic_dir = ROOT / "hypotheses" / cfg["topic"]
    topic_dir.mkdir(parents=True, exist_ok=True)
    treatment_name = cfg.get("treatment", "redistribution_system")
    outcome_name = cfg["outcome"]
    outcome_dim = {
        "distribution": ["poverty_inequality"],
        "labour": ["employment_labour"],
        "monetary": ["monetary_policy", "financialisation"],
        "housing": ["housing"],
        "institutional_quality": ["institutional_quality", "capital_flows"],
    }.get(cfg["topic"], [cfg["topic"]])
    doc = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": cfg["topic"],
        "claim": cfg["claim"],
        "evidence_type": "associational" if kind != "oecd" else "descriptive",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-periods missing the predeclared treatment or outcome",
                "retain common shocks and absorb them with year effects where the estimator is a panel FE",
            ],
        },
        "variables": {
            "outcome": [{"name": outcome_name, "source": "local pinned vintage panel", "transformation": cfg["threshold_text"]}],
            "treatment": [{"name": treatment_name, "source": "local pinned vintage panel", "transformation": "as predeclared in threshold"}],
        },
        "estimator": {
            "template": "descriptive" if kind == "oecd" else "panel_fe",
            "fixed_effects": [] if kind == "oecd" else ["country", "year"],
            "clustering": "" if kind == "oecd" else "country",
            "notes": "Generated Worker C first-tranche local-data panel verdict.",
        },
        "falsification": {
            "rule": cfg["threshold_text"],
            "test": hid,
            "threshold": cfg.get("gate", {}),
        },
        "prior_confidence": cfg["prior"],
        "disclosure": "This is a compact first-tranche screen. It predeclares magnitude and coverage gates before reading the emitted verdict, but it is not a causal natural experiment.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": period,
            "countries": ["OECD"] if kind == "oecd" else countries[:20],
            "outcome_dim": outcome_dim,
            "policy_family": ["monetary_policy"] if "policy_rate" in hid or "dsr" in hid else ["institutional_reform"],
            "treatment_tags": hid.split("_")[:5],
        },
        "notes": f"Runnable via engine/runs/{hid}/replication.py. Uses only pinned local BIS/OECD/WGI/WDI vintages.",
    }
    (topic_dir / f"{hid}.yaml").write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(doc, sort_keys=False))


def write_steelman(hid: str, cfg: dict, kind: str) -> None:
    path = ROOT / "hypotheses" / "steelman" / f"{hid}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# Steelman - {hid}

The strongest case for the claim is straightforward: the selected treatment is an observable, policy-relevant signal and the outcome is measured in an external macro panel rather than hand-coded anecdotes. The predeclared gates require both economic magnitude and coverage, so a tiny but statistically convenient coefficient is not enough.

The strongest objection is identification. These panels are deliberately low-fuss first-tranche verdicts, not causal designs. Country and year fixed effects reduce persistent country differences and common shocks where used, but they do not absorb every domestic policy cycle, banking shock, terms-of-trade event, or measurement break. For the OECD redistribution panels, the descriptive contrast is mechanically close to the tax-transfer accounting identity, so the result should be read as magnitude verification rather than a causal estimate.

If supported, the result establishes a robust local-data regularity worth promoting to a richer design. If refuted or partial, the sensible update is not that the underlying mechanism is impossible, but that this simple panel threshold is too weak, too noisy, or too aggregate to carry the claim.
"""
    path.write_text(body)


def write_run(hid: str, cfg: dict, diagnostics: dict, manifest: dict, model_df: pd.DataFrame | None, kind: str) -> None:
    out = RUNS / hid
    out.mkdir(parents=True, exist_ok=True)
    diag = {
        "hypothesis_id": hid,
        "verdict": diagnostics["verdict"],
        "verdict_detail": diagnostics["verdict_detail"],
        "threshold_text": cfg["threshold_text"],
        "thresholds": cfg.get("gate", {}),
        **{k: v for k, v in diagnostics.items() if k not in {"verdict", "verdict_detail"}},
    }
    (out / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    if model_df is not None:
        chart_col = cfg["outcome"]
        treatment = cfg.get("treatment")
        if treatment and treatment in model_df:
            chart = model_df.groupby(["year", treatment], as_index=False)[chart_col].mean().to_dict("records")
        else:
            chart = model_df.groupby("year", as_index=False)[chart_col].mean().to_dict("records")
        (out / "chart_data.json").write_text(json.dumps({"series": chart}, indent=2))
        coef = pd.DataFrame([{"hypothesis_id": hid, "term": cfg.get("treatment", "descriptive_mean"), "estimate": diagnostics.get("coefficient", diagnostics.get("mean_effect")), "std_error": diagnostics.get("standard_error_cluster_country"), "p_value": diagnostics.get("p_value"), "n_observations": diagnostics["n_observations"], "n_countries": diagnostics["n_countries"]}])
        coef.to_parquet(out / "coefficients.parquet", index=False)
    man = {
        "hypothesis_id": hid,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "runner": "scripts/generate_bis_oecd_wgi_wave.py",
        "vintages": manifest,
        "formula": cfg.get("formula", "descriptive panel contrast"),
        "threshold_text": cfg["threshold_text"],
    }
    (out / "manifest.yaml").write_text(yaml.safe_dump(man, sort_keys=False))
    wrapper = f"""#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CMD = [str(ROOT / "venv/bin/python"), str(ROOT / "scripts/generate_bis_oecd_wgi_wave.py"), "{hid}"]

if __name__ == "__main__":
    raise SystemExit(subprocess.run(CMD, cwd=ROOT).returncode)
"""
    (out / "replication.py").write_text(wrapper)
    card = result_card(hid, cfg, diag)
    (out / "result_card.md").write_text(card)


def result_card(hid: str, cfg: dict, d: dict) -> str:
    lines = [
        f"# {cfg['title']}",
        "",
        f"**Verdict:** {d['verdict']} - {d['verdict_detail']}.",
        "",
        "## Predeclared Test",
        "",
        cfg["threshold_text"],
        "",
        "## Results",
        "",
        f"- Usable panel: **{d['n_observations']:,} observations**, **{d['n_countries']} countries**.",
    ]
    if "coefficient" in d:
        lines.append(f"- Clustered FE coefficient: **{d['coefficient']:.3f}** (SE {d['standard_error_cluster_country']:.3f}, p={d['p_value']:.4f}, 95% CI [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}]).")
    if "raw_high_minus_normal_mean" in d:
        lines.append(f"- Raw high-minus-normal mean: **{d['raw_high_minus_normal_mean']:.3f}** ({d['high_mean']:.3f} vs {d['normal_mean']:.3f}); treated observations: **{d['high_count']:,}**.")
    if "mean_effect" in d:
        lines.append(f"- Mean panel contrast: **{d['mean_effect']:.3f}**; positive share: **{d['share_positive']:.3f}**.")
    if "raw_top_minus_bottom_tercile_mean" in d:
        lines.append(f"- Raw top-minus-bottom regulatory-quality tercile mean: **{d['raw_top_minus_bottom_tercile_mean']:.3f}**.")
    lines.extend([
        "",
        "## Caveats",
        "",
        "This is a compact local-data panel verdict. It is useful as a falsifiable first tranche, but it should not be read as a structural causal design without stronger identification.",
        "",
    ])
    return "\n".join(lines)


def run_one(hid: str) -> dict:
    if hid in BIS_CONFIGS:
        panel, manifest = bis_panel()
        cfg = BIS_CONFIGS[hid]
        d, diag = fit_gate(panel, cfg)
        countries = sorted(d["country"].unique().tolist())
        write_yaml(hid, cfg, countries, [int(d["year"].min()), int(d["year"].max())], "bis")
        write_steelman(hid, cfg, "bis")
        write_run(hid, cfg, diag, manifest, d, "bis")
        return {"hypothesis_id": hid, "verdict": diag["verdict"]}
    if hid in OECD_CONFIGS:
        panel, manifest = oecd_panel(hid)
        cfg = OECD_CONFIGS[hid]
        diag = descriptive_verdict(panel, cfg)
        d = panel[["country", "year", cfg["outcome"]]].dropna()
        write_yaml(hid, cfg, sorted(d["country"].unique().tolist()), [int(d["year"].min()), int(d["year"].max())], "oecd")
        write_steelman(hid, cfg, "oecd")
        write_run(hid, cfg, diag, manifest, d, "oecd")
        return {"hypothesis_id": hid, "verdict": diag["verdict"]}
    if hid in WGI_CONFIG:
        panel, manifest = wgi_panel()
        cfg = WGI_CONFIG[hid]
        d, diag = wgi_verdict(panel, cfg)
        write_yaml(hid, cfg, sorted(d["country"].unique().tolist()), [int(d["year"].min()), int(d["year"].max())], "wgi")
        write_steelman(hid, cfg, "wgi")
        write_run(hid, cfg, diag, manifest, d, "wgi")
        return {"hypothesis_id": hid, "verdict": diag["verdict"]}
    raise KeyError(hid)


def main(argv: list[str]) -> int:
    ids = list(BIS_CONFIGS) + list(OECD_CONFIGS) + list(WGI_CONFIG)
    targets = ids if len(argv) == 1 else argv[1:]
    unknown = [x for x in targets if x not in ids]
    if unknown:
        print(f"unknown ids: {unknown}", file=sys.stderr)
        return 2
    results = [run_one(hid) for hid in targets]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
