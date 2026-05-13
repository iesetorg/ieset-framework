#!/usr/bin/env python3
"""Promote and run a first BIS-heavy Batch 04 wave.

The wave intentionally uses only local vintages already on disk:
BIS credit gaps, debt-service ratios, house prices, EER, and WDI macro
outcomes. It writes hypothesis YAML, steelmen, replication wrappers, and
compact run artifacts for ten long-horizon macro-financial tests.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
BIS = ROOT / "data" / "vintages" / "bis"
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"
RUNS = ROOT / "engine" / "runs"
HYPOTHESES = ROOT / "hypotheses"
STEELMEN = HYPOTHESES / "steelman"

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

BIS_SAMPLE_ISO3 = sorted(set(BIS_ISO2_TO_ISO3.values()))

CASES = {
    "bis_credit_gap_dsr_joint_crisis_risk_panel_1999_2025": {
        "topic": "monetary",
        "claim": "Country-years with both a high BIS credit gap and high household debt-service burden are followed by larger unemployment increases.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "credit_gap_x_high_dsr",
        "continuous": "credit_gap",
        "controls": ["household_dsr", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ credit_gap_x_high_dsr + credit_gap + household_dsr + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.4, "p_max": 0.10, "mean_diff_min": 0.4, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["financial_crisis", "employment_labour"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_household_dsr_consumption_slowdown_panel_1999_2025": {
        "topic": "monetary",
        "claim": "High household debt-service burdens predict weaker private-consumption growth over the next two years.",
        "outcome": "fwd_consumption_growth_2y_avg",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "controls": ["consumption_growth"],
        "formula": "fwd_consumption_growth_2y_avg ~ high_household_dsr + household_dsr + consumption_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.8, "p_max": 0.10, "mean_diff_max": -0.8, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["gdp_growth", "financial_crisis"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_corporate_credit_boom_investment_slowdown_panel_1970_2025": {
        "topic": "growth",
        "claim": "Rapid private credit expansion predicts weaker private-investment share over the following five years.",
        "outcome": "fwd_private_investment_share_change_5y",
        "treatment": "credit_gdp_growth_5y",
        "continuous": "credit_gdp",
        "controls": ["private_investment_share", "gdp_growth"],
        "formula": "fwd_private_investment_share_change_5y ~ credit_gdp_growth_5y + credit_gdp + private_investment_share + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.03, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["productivity", "financialisation"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_credit_gap_current_account_interaction_panel_1970_2025": {
        "topic": "monetary",
        "claim": "Credit gaps are followed by larger unemployment increases when the current account is also in deficit.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "credit_gap_x_current_account_deficit",
        "continuous": "credit_gap",
        "controls": ["current_account_balance_gdp", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ credit_gap_x_current_account_deficit + credit_gap + current_account_balance_gdp + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "mean_diff_min": 0.25, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["financial_crisis", "employment_labour", "capital_flows"],
        "policy_family": ["monetary_policy", "exchange_rate_regime"],
    },
    "bis_credit_gap_property_price_interaction_panel_1970_2025": {
        "topic": "housing",
        "claim": "Credit gaps are more damaging when they coincide with real house-price booms.",
        "outcome": "fwd_real_house_price_growth_12q",
        "treatment": "credit_gap_x_house_price_boom",
        "continuous": "credit_gap",
        "controls": ["lag_real_house_price_growth_8q"],
        "formula": "fwd_real_house_price_growth_12q ~ credit_gap_x_house_price_boom + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -2.0, "p_max": 0.10, "mean_diff_max": -2.0, "min_observations": 600, "min_countries": 20},
        "outcome_dim": ["housing", "financialisation"],
        "policy_family": ["monetary_policy", "housing_policy"],
    },
    "bis_reer_appreciation_export_growth_panel_1964_2026": {
        "topic": "growth",
        "claim": "Large real exchange-rate appreciations predict weaker export growth over the following two years.",
        "outcome": "fwd_export_growth_2y_avg",
        "treatment": "large_reer_appreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["export_growth"],
        "formula": "fwd_export_growth_2y_avg ~ large_reer_appreciation + reer_appreciation_12q + export_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -1.0, "p_max": 0.10, "mean_diff_max": -1.0, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["trade_liberalisation", "capital_flows"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_reer_appreciation_industrial_share_panel_1964_2026": {
        "topic": "growth",
        "claim": "Large real exchange-rate appreciations predict later erosion in manufacturing value-added share.",
        "outcome": "fwd_manufacturing_share_change_3y",
        "treatment": "large_reer_appreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["manufacturing_share"],
        "formula": "fwd_manufacturing_share_change_3y ~ large_reer_appreciation + reer_appreciation_12q + manufacturing_share + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.3, "p_max": 0.10, "mean_diff_max": -0.3, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["industrial_capability", "trade_liberalisation"],
        "policy_family": ["exchange_rate_regime", "industrial_policy"],
    },
    "bis_reer_misalignment_current_account_repair_panel_1964_2026": {
        "topic": "monetary",
        "claim": "Large real exchange-rate appreciations are followed by current-account repair through later adjustment.",
        "outcome": "fwd_current_account_change_3y",
        "treatment": "large_reer_appreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["current_account_balance_gdp"],
        "formula": "fwd_current_account_change_3y ~ large_reer_appreciation + reer_appreciation_12q + current_account_balance_gdp + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.5, "p_max": 0.10, "mean_diff_min": 0.5, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["capital_flows", "trade_liberalisation"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_reer_devaluation_inflation_tradeoff_panel_1964_2026": {
        "topic": "monetary",
        "claim": "Large real exchange-rate depreciations are followed by higher inflation over the next two years.",
        "outcome": "fwd_inflation_2y_avg",
        "treatment": "large_reer_depreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["inflation"],
        "formula": "fwd_inflation_2y_avg ~ large_reer_depreciation + reer_appreciation_12q + inflation + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 1.0, "p_max": 0.10, "mean_diff_min": 1.0, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["inflation", "currency_purchasing_power"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_reer_volatility_investment_drag_panel_1964_2026": {
        "topic": "growth",
        "claim": "Higher real exchange-rate volatility predicts lower private-investment share.",
        "outcome": "fwd_private_investment_share_change_3y",
        "treatment": "high_reer_volatility",
        "continuous": "reer_volatility_12q",
        "controls": ["private_investment_share", "gdp_growth"],
        "formula": "fwd_private_investment_share_change_3y ~ high_reer_volatility + reer_volatility_12q + private_investment_share + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["productivity", "capital_flows"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_credit_gap_unemployment_lag_panel_1970_2025": {
        "topic": "monetary",
        "claim": "High BIS credit-gap episodes predict unemployment increases over the following two years.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ high_credit_gap + credit_gap + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.25, "p_max": 0.10, "mean_diff_min": 0.25, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["financial_crisis", "employment_labour"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_credit_gap_consumption_slowdown_panel_1970_2025": {
        "topic": "monetary",
        "claim": "High BIS credit-gap episodes predict weaker private-consumption growth over the following two years.",
        "outcome": "fwd_consumption_growth_2y_avg",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["consumption_growth"],
        "formula": "fwd_consumption_growth_2y_avg ~ high_credit_gap + credit_gap + consumption_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["gdp_growth", "financial_crisis"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_credit_gap_private_investment_slowdown_panel_1970_2025": {
        "topic": "growth",
        "claim": "High BIS credit-gap episodes predict weaker private-investment share over the following three years.",
        "outcome": "fwd_private_investment_share_change_3y",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["private_investment_share", "gdp_growth"],
        "formula": "fwd_private_investment_share_change_3y ~ high_credit_gap + credit_gap + private_investment_share + gdp_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.5, "p_max": 0.10, "mean_diff_max": -0.5, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["productivity", "financialisation"],
        "policy_family": ["monetary_policy", "regulation"],
    },
    "bis_dsr_current_account_deficit_unemployment_panel_1999_2025": {
        "topic": "monetary",
        "claim": "Household debt-service stress predicts larger unemployment increases when the current account is also in deficit.",
        "outcome": "fwd_unemployment_change_2y",
        "treatment": "high_dsr_x_current_account_deficit",
        "continuous": "household_dsr",
        "controls": ["current_account_balance_gdp", "unemployment_rate"],
        "formula": "fwd_unemployment_change_2y ~ high_dsr_x_current_account_deficit + household_dsr + current_account_balance_gdp + unemployment_rate + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.35, "p_max": 0.10, "mean_diff_min": 0.35, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["financial_crisis", "employment_labour", "capital_flows"],
        "policy_family": ["monetary_policy", "exchange_rate_regime"],
    },
    "bis_dsr_house_price_boom_reversal_panel_1999_2025": {
        "topic": "housing",
        "claim": "House-price booms reverse more sharply when household debt-service burdens are high.",
        "outcome": "fwd_real_house_price_growth_12q",
        "treatment": "high_dsr_x_house_price_boom",
        "continuous": "household_dsr",
        "controls": ["lag_real_house_price_growth_8q"],
        "formula": "fwd_real_house_price_growth_12q ~ high_dsr_x_house_price_boom + household_dsr + lag_real_house_price_growth_8q + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -2.0, "p_max": 0.10, "mean_diff_max": -2.0, "min_observations": 450, "min_countries": 15},
        "outcome_dim": ["housing", "financialisation"],
        "policy_family": ["monetary_policy", "housing_policy"],
    },
    "bis_reer_volatility_export_drag_panel_1964_2026": {
        "topic": "growth",
        "claim": "High real exchange-rate volatility predicts weaker export growth.",
        "outcome": "fwd_export_growth_2y_avg",
        "treatment": "high_reer_volatility",
        "continuous": "reer_volatility_12q",
        "controls": ["export_growth"],
        "formula": "fwd_export_growth_2y_avg ~ high_reer_volatility + reer_volatility_12q + export_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -1.0, "p_max": 0.10, "mean_diff_max": -1.0, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["trade_liberalisation", "capital_flows"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_reer_depreciation_current_account_repair_panel_1964_2026": {
        "topic": "monetary",
        "claim": "Large real exchange-rate depreciations predict current-account improvement over the following three years.",
        "outcome": "fwd_current_account_change_3y",
        "treatment": "large_reer_depreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["current_account_balance_gdp"],
        "formula": "fwd_current_account_change_3y ~ large_reer_depreciation + reer_appreciation_12q + current_account_balance_gdp + C(country) + C(year)",
        "direction": "positive",
        "gate": {"coef_min": 0.5, "p_max": 0.10, "mean_diff_min": 0.5, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["capital_flows", "trade_liberalisation"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_reer_appreciation_inflation_relief_panel_1964_2026": {
        "topic": "monetary",
        "claim": "Large real exchange-rate appreciations predict lower inflation over the following two years.",
        "outcome": "fwd_inflation_2y_avg",
        "treatment": "large_reer_appreciation",
        "continuous": "reer_appreciation_12q",
        "controls": ["inflation"],
        "formula": "fwd_inflation_2y_avg ~ large_reer_appreciation + reer_appreciation_12q + inflation + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -1.0, "p_max": 0.10, "mean_diff_max": -1.0, "min_observations": 900, "min_countries": 20},
        "outcome_dim": ["inflation", "currency_purchasing_power"],
        "policy_family": ["exchange_rate_regime", "monetary_policy"],
    },
    "bis_credit_gap_export_growth_drag_panel_1970_2025": {
        "topic": "growth",
        "claim": "High credit-gap episodes predict weaker export growth as domestic credit booms unwind.",
        "outcome": "fwd_export_growth_2y_avg",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["export_growth"],
        "formula": "fwd_export_growth_2y_avg ~ high_credit_gap + credit_gap + export_growth + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.75, "p_max": 0.10, "mean_diff_max": -0.75, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["trade_liberalisation", "financialisation"],
        "policy_family": ["monetary_policy", "exchange_rate_regime"],
    },
    "bis_credit_gap_manufacturing_share_drag_panel_1970_2025": {
        "topic": "growth",
        "claim": "High credit-gap episodes predict later manufacturing-share erosion.",
        "outcome": "fwd_manufacturing_share_change_3y",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "controls": ["manufacturing_share"],
        "formula": "fwd_manufacturing_share_change_3y ~ high_credit_gap + credit_gap + manufacturing_share + C(country) + C(year)",
        "direction": "negative",
        "gate": {"coef_max": -0.3, "p_max": 0.10, "mean_diff_max": -0.3, "min_observations": 700, "min_countries": 20},
        "outcome_dim": ["industrial_capability", "financialisation"],
        "policy_family": ["monetary_policy", "industrial_policy"],
    },
}


def latest(root: Path, stem: str) -> Path:
    files = sorted(root.glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {root}/{stem}@*.parquet")
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


def add_forward_log_growth(df: pd.DataFrame, value_col: str, horizons: list[int], prefix: str) -> pd.DataFrame:
    out = df.sort_values(["country", "q"]).copy()
    for h in horizons:
        future = out.groupby("country")[value_col].shift(-h)
        past = out.groupby("country")[value_col].shift(h)
        out[f"fwd_{prefix}_growth_{h}q"] = 100 * (np.log(future) - np.log(out[value_col]))
        out[f"lag_{prefix}_growth_{h}q"] = 100 * (np.log(out[value_col]) - np.log(past))
    return out


def wdi_series(stem: str, name: str) -> tuple[pd.DataFrame, dict]:
    path = latest(WDI, stem)
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "value"]].rename(columns={"country_iso3": "country", "value": name}).copy()
    out[name] = pd.to_numeric(out[name], errors="coerce")
    out = out[out["country"].astype(str).str.fullmatch(r"[A-Z]{3}")].dropna(subset=[name])
    out["year"] = out["year"].astype(int)
    return out, {
        "publisher": "world_bank_wdi",
        "series": stem,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
    }


def build_panel() -> tuple[pd.DataFrame, dict]:
    paths = {name: latest(BIS, name) for name in ["WS_CREDIT_GAP", "WS_DSR", "WS_SPP", "WS_EER"]}
    credit_raw = pd.read_parquet(paths["WS_CREDIT_GAP"])
    gap = bis_quarterly(credit_raw[credit_raw["CG_DTYPE"].eq("C")], "BORROWERS_CTY").rename(columns={"value": "credit_gap"})
    level = bis_quarterly(credit_raw[credit_raw["CG_DTYPE"].eq("B")], "BORROWERS_CTY").rename(columns={"value": "credit_gdp"})
    level = level.sort_values(["country", "q"])
    level["credit_gdp_growth_5y"] = level["credit_gdp"] - level.groupby("country")["credit_gdp"].shift(20)

    dsr_raw = pd.read_parquet(paths["WS_DSR"])
    dsr = bis_quarterly(dsr_raw[dsr_raw["DSR_BORROWERS"].eq("H")], "BORROWERS_CTY").rename(columns={"value": "household_dsr"})
    p75 = dsr.groupby("country")["household_dsr"].quantile(0.75).rename("dsr_p75")
    dsr = dsr.merge(p75, on="country", how="left")
    dsr["high_household_dsr"] = ((dsr["household_dsr"] >= 12.0) & (dsr["household_dsr"] >= dsr["dsr_p75"])).astype(int)

    spp_raw = pd.read_parquet(paths["WS_SPP"])
    house = bis_quarterly(spp_raw[spp_raw["VALUE"].eq("R")], "REF_AREA").rename(columns={"value": "real_house_price"})
    house = add_forward_log_growth(house, "real_house_price", [8, 12], "real_house_price")
    house["house_price_boom"] = (house["lag_real_house_price_growth_8q"] >= 10.0).astype(int)

    eer_raw = pd.read_parquet(paths["WS_EER"])
    eer_m = eer_raw[
        eer_raw["FREQ"].eq("M")
        & eer_raw["EER_TYPE"].eq("R")
        & eer_raw["EER_BASKET"].eq("B")
    ][["REF_AREA", "period", "value"]].copy()
    eer_m["country"] = eer_m["REF_AREA"].map(BIS_ISO2_TO_ISO3)
    eer_m["date"] = pd.to_datetime(eer_m["period"] + "-01", errors="coerce")
    eer_m["q"] = eer_m["date"].dt.year * 4 + ((eer_m["date"].dt.month - 1) // 3 + 1)
    eer = (
        eer_m.dropna(subset=["country", "q", "value"])
        .groupby(["country", "q"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "reer"})
    )
    eer["year"] = eer["q"].map(qyear)
    eer = add_forward_log_growth(eer, "reer", [8, 12], "reer")
    eer = eer.rename(columns={"lag_reer_growth_12q": "reer_appreciation_12q"})
    eer["large_reer_appreciation"] = (eer["reer_appreciation_12q"] >= 15.0).astype(int)
    eer["large_reer_depreciation"] = (eer["reer_appreciation_12q"] <= -15.0).astype(int)
    eer["reer_volatility_12q"] = eer.sort_values(["country", "q"]).groupby("country")["reer"].pct_change().mul(100).groupby(eer["country"]).rolling(12).std().reset_index(level=0, drop=True)
    vol75 = eer.groupby("country")["reer_volatility_12q"].quantile(0.75).rename("reer_volatility_p75")
    eer = eer.merge(vol75, on="country", how="left")
    eer["high_reer_volatility"] = (eer["reer_volatility_12q"] >= eer["reer_volatility_p75"]).astype(int)

    panel = gap[["country", "q", "year", "credit_gap"]]
    panel = panel.merge(level[["country", "q", "year", "credit_gdp", "credit_gdp_growth_5y"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(dsr[["country", "q", "year", "household_dsr", "high_household_dsr"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(house[["country", "q", "year", "fwd_real_house_price_growth_12q", "lag_real_house_price_growth_8q", "house_price_boom"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(eer[["country", "q", "year", "reer_appreciation_12q", "large_reer_appreciation", "large_reer_depreciation", "reer_volatility_12q", "high_reer_volatility"]], on=["country", "q", "year"], how="outer")
    panel["high_credit_gap"] = (panel["credit_gap"] >= 10.0).astype(int)
    panel["credit_gap_x_high_dsr"] = panel["high_credit_gap"] * panel["high_household_dsr"]
    panel["credit_gap_x_house_price_boom"] = panel["high_credit_gap"] * panel["house_price_boom"]

    wdi_specs = [
        ("SL.UEM.TOTL.ZS", "unemployment_rate"),
        ("NE.CON.PRVT.KD.ZG", "consumption_growth"),
        ("NE.GDI.FPRV.ZS", "private_investment_share"),
        ("NY.GDP.MKTP.KD.ZG", "gdp_growth"),
        ("BN.CAB.XOKA.GD.ZS", "current_account_balance_gdp"),
        ("NE.EXP.GNFS.KD.ZG", "export_growth"),
        ("NV.IND.MANF.ZS", "manufacturing_share"),
        ("FP.CPI.TOTL.ZG", "inflation"),
    ]
    manifest = {
        name: {"publisher": "bis", "series": name, "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        for name, path in paths.items()
    }
    for stem, name in wdi_specs:
        frame, meta = wdi_series(stem, name)
        manifest[stem] = meta
        panel = panel.merge(frame, on=["country", "year"], how="left")

    annual = panel[
        [
            "country", "year", "unemployment_rate", "consumption_growth", "private_investment_share",
            "current_account_balance_gdp", "export_growth", "manufacturing_share", "inflation",
        ]
    ].drop_duplicates().sort_values(["country", "year"])
    annual["fwd_unemployment_change_2y"] = annual.groupby("country")["unemployment_rate"].shift(-2) - annual["unemployment_rate"]
    annual["fwd_consumption_growth_2y_avg"] = (annual.groupby("country")["consumption_growth"].shift(-1) + annual.groupby("country")["consumption_growth"].shift(-2)) / 2
    annual["fwd_private_investment_share_change_5y"] = annual.groupby("country")["private_investment_share"].shift(-5) - annual["private_investment_share"]
    annual["fwd_private_investment_share_change_3y"] = annual.groupby("country")["private_investment_share"].shift(-3) - annual["private_investment_share"]
    annual["fwd_current_account_change_3y"] = annual.groupby("country")["current_account_balance_gdp"].shift(-3) - annual["current_account_balance_gdp"]
    annual["fwd_export_growth_2y_avg"] = (annual.groupby("country")["export_growth"].shift(-1) + annual.groupby("country")["export_growth"].shift(-2)) / 2
    annual["fwd_manufacturing_share_change_3y"] = annual.groupby("country")["manufacturing_share"].shift(-3) - annual["manufacturing_share"]
    annual["fwd_inflation_2y_avg"] = (annual.groupby("country")["inflation"].shift(-1) + annual.groupby("country")["inflation"].shift(-2)) / 2
    panel = panel.merge(
        annual[
            [
                "country", "year", "fwd_unemployment_change_2y", "fwd_consumption_growth_2y_avg",
                "fwd_private_investment_share_change_5y", "fwd_private_investment_share_change_3y",
                "fwd_current_account_change_3y", "fwd_export_growth_2y_avg",
                "fwd_manufacturing_share_change_3y", "fwd_inflation_2y_avg",
            ]
        ],
        on=["country", "year"],
        how="left",
    )
    panel["current_account_deficit"] = (panel["current_account_balance_gdp"] < 0).astype(int)
    panel["credit_gap_x_current_account_deficit"] = panel["high_credit_gap"] * panel["current_account_deficit"]
    panel["high_dsr_x_current_account_deficit"] = panel["high_household_dsr"] * panel["current_account_deficit"]
    panel["high_dsr_x_house_price_boom"] = panel["high_household_dsr"] * panel["house_price_boom"]
    return panel, manifest


def verdict_from(direction: str, gate: dict, beta: float, p: float, diff: float, n_obs: int, n_countries: int) -> tuple[str, str]:
    enough = n_obs >= gate["min_observations"] and n_countries >= gate["min_countries"]
    if not enough:
        return "INCONCLUSIVE_DATA_PENDING", "insufficient coverage for the predeclared gate"
    if direction == "positive":
        effect = beta >= gate["coef_min"] and p <= gate["p_max"]
        raw = diff >= gate["mean_diff_min"]
    else:
        effect = beta <= gate["coef_max"] and p <= gate["p_max"]
        raw = diff <= gate["mean_diff_max"]
    if effect and raw:
        return "SUPPORTED", "regression and raw contrast both clear the predeclared gates"
    if effect or raw:
        return "PARTIAL", "one of the regression or raw-contrast gates clears, but not both"
    return "REFUTED", "neither the regression nor raw-contrast gate clears"


def fit_case(hid: str, cfg: dict, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
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
    verdict, reason = verdict_from(cfg["direction"], cfg["gate"], beta, p, diff, len(d), d["country"].nunique())
    return d, {
        "hypothesis_id": hid,
        "verdict_label": verdict,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_countries": int(d["country"].nunique()),
        "outcome": cfg["outcome"],
        "treatment": term,
        "coefficient": beta,
        "standard_error_cluster_country": se,
        "p_value": p,
        "ci95": [ci_low, ci_high],
        "raw_treated_minus_control_mean": diff,
        "control_mean": base,
        "treated_mean": high,
        "treated_count": int(group.get(1, {}).get("count", 0)),
        "gate": cfg["gate"],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/promote_bis_batch04_wave_2026_05_12.py",
    }


def write_hypothesis(hid: str, cfg: dict) -> None:
    out_dir = HYPOTHESES / cfg["topic"]
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": cfg["topic"],
        "claim": cfg["claim"],
        "evidence_type": "associational",
        "sample": {
            "countries": BIS_SAMPLE_ISO3,
            "period": [1964, 2026],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing the predeclared BIS treatment",
                "drop country-years missing the WDI outcome or controls",
                "require forward outcome coverage before evaluating the row",
            ],
        },
        "variables": {
            "outcome": [{"name": cfg["outcome"], "source": "constructed: forward outcome from WDI or BIS local vintage", "transformation": "forward_change_or_forward_average"}],
            "treatment": [{"name": cfg["treatment"], "source": "bis:WS_CREDIT_GAP; bis:WS_DSR; bis:WS_EER; bis:WS_SPP", "transformation": "threshold_or_interaction_predeclared_in_runner"}],
            "controls": [{"name": c, "source": "world_bank_wdi or BIS local vintage", "transformation": "level"} for c in cfg["controls"]],
        },
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": "Compact panel screen with country and calendar-year fixed effects. Standard errors clustered by country.",
        },
        "falsification": {
            "rule": f"Supported only if the coefficient on {cfg['treatment']} and the raw treated-control contrast clear the predeclared direction and magnitude gates.",
            "test": hid,
            "threshold": json.dumps(cfg["gate"], sort_keys=True),
        },
        "prior_confidence": 0.58,
        "disclosure": "This is a predictive panel screen, not a structural causal estimate. It is designed to test whether broad macro-financial signals generalise across countries and time.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {
            "period": [1964, 2026],
            "countries": ["GLOBAL"],
            "outcome_dim": cfg["outcome_dim"],
            "policy_family": cfg["policy_family"],
            "treatment_tags": [cfg["treatment"]],
        },
        "notes": f"Generated and runnable via engine/runs/{hid}/replication.py from local BIS/WDI vintages.",
    }
    path = out_dir / f"{hid}.yaml"
    path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(doc, sort_keys=False, allow_unicode=False))

    STEELMEN.mkdir(parents=True, exist_ok=True)
    (STEELMEN / f"{hid}.md").write_text(
        f"# Steelman - {hid}\n\n"
        f"The strongest version of the claim is: {cfg['claim']}\n\n"
        "The skeptical case is that BIS macro-financial variables may proxy for omitted local policy, banking structure, terms-of-trade shocks, or measurement changes. "
        "A fair test therefore needs broad country coverage, fixed effects, transparent thresholds, and a result card that does not treat predictive association as causality.\n"
    )


def write_run(hid: str, cfg: dict, d: pd.DataFrame, diag: dict, manifest: dict) -> None:
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    coef_df = pd.DataFrame([{
        "hypothesis_id": hid,
        "term": cfg["treatment"],
        "estimate": diag["coefficient"],
        "std_error": diag["standard_error_cluster_country"],
        "p_value": diag["p_value"],
        "ci95_low": diag["ci95"][0],
        "ci95_high": diag["ci95"][1],
        "n_observations": diag["n_observations"],
        "n_countries": diag["n_countries"],
    }])
    coef_df.to_parquet(out_dir / "coefficients.parquet", index=False)
    chart = d.groupby(["year", cfg["treatment"]], as_index=False)[cfg["outcome"]].mean().rename(columns={cfg["outcome"]: "mean_outcome"})
    (out_dir / "chart_data.json").write_text(json.dumps({"series": chart.to_dict("records")}, indent=2))
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": diag["run_utc"],
        "runner": diag["runner"],
        "formula": cfg["formula"],
        "vintages": manifest,
    }, sort_keys=False))
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import subprocess, sys\n\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_bis_batch04_wave_2026_05_12.py'), '{hid}']))\n"
    )
    (out_dir / "replication.py").write_text(wrapper)
    card = f"""# Result card - {hid}

**Verdict:** {diag['verdict_label']} - {diag['verdict_reason']}.

## Plain-English Claim

{cfg['claim']}

## What Was Measured

- Outcome: `{cfg['outcome']}`.
- Treatment: `{cfg['treatment']}`.
- Controls: {', '.join(f'`{c}`' for c in cfg['controls'])}.

## Results

- Usable panel: **{diag['n_observations']:,} observations**, **{diag['n_countries']} countries**.
- Coefficient on treatment: **{diag['coefficient']:.4f}** (SE {diag['standard_error_cluster_country']:.4f}, p={diag['p_value']:.4f}).
- Raw treated-control mean difference: **{diag['raw_treated_minus_control_mean']:.4f}**.
- Treated observations: **{diag['treated_count']:,}**.

## Specification

`{cfg['formula']}`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
"""
    (out_dir / "result_card.md").write_text(card)


def run_one(hid: str) -> dict:
    if hid not in CASES:
        raise KeyError(f"unknown case {hid}")
    panel, manifest = build_panel()
    cfg = CASES[hid]
    write_hypothesis(hid, cfg)
    d, diag = fit_case(hid, cfg, panel)
    write_run(hid, cfg, d, diag, manifest)
    return diag


def main(argv: list[str]) -> int:
    targets = argv[1:] or list(CASES)
    results = []
    for hid in targets:
        diag = run_one(hid)
        results.append({"hypothesis_id": hid, "verdict": diag["verdict_label"], "reason": diag["verdict_reason"]})
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
