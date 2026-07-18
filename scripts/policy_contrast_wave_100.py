#!/usr/bin/env python3
"""Preregister, run, and audit 100 policy-contrast hypotheses.

The wave is deliberately split into commands so git history can prove that
specifications preceded results:

    python3 scripts/policy_contrast_wave_100.py --write-prereg
    # commit specifications and steelmen
    python3 scripts/policy_contrast_wave_100.py --run-all
    # commit run artifacts
    python3 scripts/generate_evidence_packets.py --run <id> ...
    python3 scripts/check_preregistration.py --write-index
    python3 scripts/policy_contrast_wave_100.py --write-audit

No coefficient is estimated by --preflight or --write-prereg. Those commands
only verify coverage, variation, and the predeclared contrast gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES = ROOT / "hypotheses"
STEELMEN = HYPOTHESES / "steelman"
RUNS = ROOT / "engine" / "runs"
AUDITS = ROOT / "engine" / "audits"
WAVE_ID = "policy_contrast_wave_100_2026_07_18"
REGISTRY_JSON = AUDITS / f"{WAVE_ID}_registry.json"
REGISTRY_MD = AUDITS / f"{WAVE_ID}_registry.md"
AUDIT_JSON = AUDITS / f"{WAVE_ID}_graduation.json"
AUDIT_MD = AUDITS / f"{WAVE_ID}_graduation.md"
RUNNER_REL = "scripts/policy_contrast_wave_100.py"
P_MAX = 0.10
US_UNITS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
    "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY",
    "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX",
    "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}

STATE_MIN_WAGE = Path("data/derived/us_state_minimum_wage_treatment_panel.parquet")
STATE_LABOR = Path("data/derived/us_state_labor_outcome_panel.parquet")
STATE_FISCAL = Path("data/derived/us_state_gov_finances_panel.parquet")
STATE_INCIDENCE = Path("data/derived/us_state_acs_saipe_incidence_panel.parquet")
STATE_HOUSING = Path("data/derived/us_state_housing_supply_price_panel.parquet")

EFW_PATHS = {
    "size_government": Path(
        "data/vintages/fraser_efw/size_of_government@2026-05-02T220000Z.parquet"
    ),
    "legal_rights": Path(
        "data/vintages/fraser_efw/legal_system_property_rights@2026-05-02T220000Z.parquet"
    ),
    "sound_money": Path(
        "data/vintages/fraser_efw/sound_money@2026-05-02T220000Z.parquet"
    ),
    "trade_freedom": Path(
        "data/vintages/fraser_efw/freedom_to_trade_internationally@2026-05-02T220000Z.parquet"
    ),
    "regulation": Path(
        "data/vintages/fraser_efw/regulation@2026-05-02T220000Z.parquet"
    ),
}

WDI_PATHS = {
    "gdp_growth": Path(
        "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet"
    ),
    "employment": Path(
        "data/vintages/world_bank_wdi/SL.EMP.TOTL.SP.ZS@2026-05-05T194751Z.parquet"
    ),
    "unemployment": Path(
        "data/vintages/world_bank_wdi/SL.UEM.TOTL.ZS@2026-05-05T200521Z.parquet"
    ),
    "investment": Path(
        "data/vintages/world_bank_wdi/NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet"
    ),
    "manufacturing": Path(
        "data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet"
    ),
    "fdi": Path(
        "data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-05-05T195106Z.parquet"
    ),
    "life_expectancy": Path(
        "data/vintages/world_bank_wdi/SP.DYN.LE00.IN@2026-05-05T194852Z.parquet"
    ),
    "under5_mortality": Path(
        "data/vintages/world_bank_wdi/SH.DYN.MORT@2026-05-05T194907Z.parquet"
    ),
    "private_credit": Path(
        "data/vintages/world_bank_wdi/FS.AST.PRVT.GD.ZS@2026-05-05T194720Z.parquet"
    ),
    "hightech_exports": Path(
        "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet"
    ),
    "gdp_pc_level": Path(
        "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet"
    ),
}

MIN_WAGE_TREATMENTS = {
    "binding_premium": {
        "label": "state minimum-wage premium above the federal floor",
        "variable": "binding_premium",
        "transformation": "max(effective state minimum wage minus federal minimum wage, 0), dollars",
        "contrast_min": 0.25,
        "tags": ["state_minimum_wage", "federal_floor", "binding_premium"],
    },
    "bite_ratio": {
        "label": "state minimum-wage bite relative to the state wage denominator",
        "variable": "bite_ratio",
        "transformation": "effective minimum wage divided by the published state wage denominator",
        "contrast_min": 0.02,
        "tags": ["state_minimum_wage", "minimum_wage_bite", "wage_floor"],
    },
    "increase_event": {
        "label": "a state minimum-wage increase event",
        "variable": "increase_event",
        "transformation": "indicator equal to one when the effective minimum wage rises from the prior year",
        "contrast_min": 1.0,
        "tags": ["state_minimum_wage", "minimum_wage_increase", "policy_event"],
    },
}

MIN_WAGE_OUTCOMES = {
    "unemployment": {
        "label": "state unemployment rate",
        "column": "unemployment_rate",
        "transformation": "annual rate in percentage points",
        "sign": "+",
        "topic": "labour",
        "dims": ["employment_labour"],
        "phrase": "higher unemployment",
    },
    "employment_ratio": {
        "label": "state employment-to-population ratio",
        "column": "employment_population_ratio",
        "transformation": "annual ratio in percentage points",
        "sign": "-",
        "topic": "labour",
        "dims": ["employment_labour"],
        "phrase": "a lower employment-to-population ratio",
    },
    "median_wage": {
        "label": "state median hourly wage",
        "column": "median_hourly_wage",
        "transformation": "natural log of annual median hourly wage",
        "sign": "+",
        "topic": "labour",
        "dims": ["wage_stagnation", "employment_labour"],
        "phrase": "higher median hourly wages",
    },
    "p10_wage": {
        "label": "state tenth-percentile hourly wage",
        "column": "p10_hourly_wage",
        "transformation": "natural log of annual tenth-percentile hourly wage",
        "sign": "+",
        "topic": "distribution",
        "dims": ["wage_stagnation", "poverty_inequality"],
        "phrase": "higher tenth-percentile hourly wages",
    },
    "median_wage_growth": {
        "label": "state median-hourly-wage growth",
        "column": "median_hourly_wage",
        "transformation": "100 times the within-state annual log difference",
        "sign": "+",
        "topic": "labour",
        "dims": ["wage_stagnation", "employment_labour"],
        "phrase": "faster median-hourly-wage growth",
    },
    "food_employment_growth": {
        "label": "QCEW food-service employment growth",
        "column": "qcew_food_service_employment",
        "transformation": "100 times the within-state annual log difference",
        "sign": "-",
        "topic": "labour",
        "dims": ["employment_labour"],
        "phrase": "slower food-service employment growth",
    },
    "total_weekly_wage": {
        "label": "QCEW average weekly wage",
        "column": "qcew_avg_weekly_wage",
        "transformation": "natural log of annual average weekly wage",
        "sign": "+",
        "topic": "labour",
        "dims": ["wage_stagnation", "employment_labour"],
        "phrase": "higher average weekly wages",
    },
    "food_weekly_wage": {
        "label": "QCEW food-service average weekly wage",
        "column": "qcew_food_service_avg_weekly_wage",
        "transformation": "natural log of annual food-service average weekly wage",
        "sign": "+",
        "topic": "labour",
        "dims": ["wage_stagnation", "employment_labour"],
        "phrase": "higher food-service average weekly wages",
    },
    "food_establishment_growth": {
        "label": "QCEW food-service establishment growth",
        "column": "qcew_food_service_establishments",
        "transformation": "100 times the within-state annual log difference",
        "sign": "-",
        "topic": "labour",
        "dims": ["employment_labour", "competition_concentration"],
        "phrase": "slower food-service establishment growth",
    },
    "poverty": {
        "label": "SAIPE all-ages poverty rate",
        "column": "saipe_poverty_rate_all_ages",
        "transformation": "annual rate in percentage points",
        "sign": "-",
        "topic": "distribution",
        "dims": ["poverty_inequality"],
        "phrase": "a lower all-ages poverty rate",
    },
}

FISCAL_TREATMENTS = {
    "tax_revenue_share": {
        "label": "total tax revenue as a share of total state revenue",
        "numerator": "total_tax_revenue",
        "signs": {
            "poverty": "-",
            "median_income": "+",
            "employment_ratio": "+",
            "permit_units": "-",
            "hpi_growth": "+",
        },
        "tags": ["state_tax_revenue", "fiscal_capacity", "tax_mix"],
    },
    "sales_tax_share": {
        "label": "sales and gross-receipts tax revenue as a share of total state revenue",
        "numerator": "sales_gross_receipts_tax",
        "signs": {
            "poverty": "+",
            "median_income": "-",
            "employment_ratio": "-",
            "permit_units": "-",
            "hpi_growth": "-",
        },
        "tags": ["state_sales_tax", "consumption_tax", "tax_mix"],
    },
    "income_tax_share": {
        "label": "individual-income-tax revenue as a share of total state revenue",
        "numerator": "individual_income_tax",
        "signs": {
            "poverty": "-",
            "median_income": "+",
            "employment_ratio": "-",
            "permit_units": "-",
            "hpi_growth": "-",
        },
        "tags": ["state_income_tax", "income_tax", "tax_mix"],
    },
    "debt_revenue_ratio": {
        "label": "outstanding state debt relative to total state revenue",
        "numerator": "total_debt_outstanding",
        "signs": {
            "poverty": "+",
            "median_income": "-",
            "employment_ratio": "-",
            "permit_units": "-",
            "hpi_growth": "-",
        },
        "tags": ["state_debt", "debt_burden", "fiscal_policy"],
    },
}

FISCAL_OUTCOMES = {
    "poverty": {
        "label": "next-year SAIPE all-ages poverty rate",
        "column": "saipe_poverty_rate_all_ages",
        "transformation": "next-year rate in percentage points",
        "topic": "distribution",
        "dims": ["poverty_inequality"],
        "positive": "a higher next-year poverty rate",
        "negative": "a lower next-year poverty rate",
    },
    "median_income": {
        "label": "next-year SAIPE median household income",
        "column": "saipe_median_household_income",
        "transformation": "natural log of next-year median household income",
        "topic": "distribution",
        "dims": ["poverty_inequality", "wage_stagnation"],
        "positive": "higher next-year median household income",
        "negative": "lower next-year median household income",
    },
    "employment_ratio": {
        "label": "next-year employment-to-population ratio",
        "column": "employment_population_ratio",
        "transformation": "next-year ratio in percentage points",
        "topic": "labour",
        "dims": ["employment_labour"],
        "positive": "a higher next-year employment-to-population ratio",
        "negative": "a lower next-year employment-to-population ratio",
    },
    "permit_units": {
        "label": "next-year permitted housing units",
        "column": "bps_total_permit_units",
        "transformation": "natural log of next-year permitted housing units",
        "topic": "housing",
        "dims": ["housing"],
        "positive": "more next-year permitted housing units",
        "negative": "fewer next-year permitted housing units",
    },
    "hpi_growth": {
        "label": "next-year FHFA house-price growth",
        "column": "hpi_growth",
        "transformation": "100 times the next-year within-state annual log difference",
        "topic": "housing",
        "dims": ["housing"],
        "positive": "faster next-year house-price growth",
        "negative": "slower next-year house-price growth",
    },
}

EFW_TREATMENTS = {
    "size_government": {
        "label": "Fraser size-of-government freedom score",
        "source": "fraser_efw:size_of_government",
        "topic": "fiscal",
        "channel": "fiscal",
        "policy_family": ["fiscal_policy", "tax_policy"],
        "tags": ["size_of_government", "fiscal_freedom", "tax_burden"],
        "prior": 0.52,
    },
    "legal_rights": {
        "label": "Fraser legal-system and property-rights score",
        "source": "fraser_efw:legal_system_property_rights",
        "topic": "institutional_quality",
        "channel": "institutional",
        "policy_family": ["institutional_reform", "regulation"],
        "tags": ["property_rights", "legal_system", "contract_enforcement"],
        "prior": 0.58,
    },
    "sound_money": {
        "label": "Fraser sound-money score",
        "source": "fraser_efw:sound_money",
        "topic": "monetary",
        "channel": "monetary",
        "policy_family": ["monetary_policy"],
        "tags": ["sound_money", "monetary_stability", "inflation_discipline"],
        "prior": 0.56,
    },
    "trade_freedom": {
        "label": "Fraser freedom-to-trade-internationally score",
        "source": "fraser_efw:freedom_to_trade_internationally",
        "topic": "trade",
        "channel": "regulatory",
        "policy_family": ["trade_policy", "competition_policy"],
        "tags": ["trade_freedom", "market_access", "trade_policy"],
        "prior": 0.55,
    },
    "regulation": {
        "label": "Fraser regulation-freedom score",
        "source": "fraser_efw:regulation",
        "topic": "regulatory",
        "channel": "regulatory",
        "policy_family": ["regulation", "competition_policy"],
        "tags": ["regulatory_freedom", "market_entry", "competition"],
        "prior": 0.54,
    },
}

INTERNATIONAL_OUTCOMES = {
    "gdp_growth": {
        "label": "mean annual real GDP per capita growth",
        "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG",
        "sign": "+",
        "dims": ["gdp_growth", "productivity"],
        "transformation": "country mean over 2006-2023",
        "phrase": "faster average real GDP per capita growth",
        "mode": "mean",
    },
    "employment": {
        "label": "employment-to-population ratio change",
        "source": "world_bank_wdi:SL.EMP.TOTL.SP.ZS",
        "sign": "+",
        "dims": ["employment_labour"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in the employment-to-population ratio",
        "mode": "change",
    },
    "unemployment": {
        "label": "unemployment-rate change",
        "source": "world_bank_wdi:SL.UEM.TOTL.ZS",
        "sign": "-",
        "dims": ["employment_labour"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger decline in unemployment",
        "mode": "change",
    },
    "investment": {
        "label": "fixed-investment-share change",
        "source": "world_bank_wdi:NE.GDI.FTOT.ZS",
        "sign": "+",
        "dims": ["capital_flows", "gdp_growth"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in fixed investment as a share of GDP",
        "mode": "change",
    },
    "manufacturing": {
        "label": "manufacturing-value-added-share change",
        "source": "world_bank_wdi:NV.IND.MANF.ZS",
        "sign": "+",
        "dims": ["industrial_capability", "productivity"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in manufacturing value added as a share of GDP",
        "mode": "change",
    },
    "fdi": {
        "label": "mean FDI net inflows as a share of GDP",
        "source": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
        "sign": "+",
        "dims": ["capital_flows", "trade_liberalisation"],
        "transformation": "country mean over 2006-2023",
        "phrase": "higher average FDI inflows as a share of GDP",
        "mode": "mean",
    },
    "life_expectancy": {
        "label": "life-expectancy change",
        "source": "world_bank_wdi:SP.DYN.LE00.IN",
        "sign": "+",
        "dims": ["life_expectancy_health"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in life expectancy",
        "mode": "change",
    },
    "under5_mortality": {
        "label": "under-five-mortality change",
        "source": "world_bank_wdi:SH.DYN.MORT",
        "sign": "-",
        "dims": ["life_expectancy_health", "poverty_inequality"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger decline in under-five mortality",
        "mode": "change",
    },
    "private_credit": {
        "label": "private-credit-depth change",
        "source": "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "sign": "+",
        "dims": ["financialisation", "capital_flows"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in private credit as a share of GDP",
        "mode": "change",
    },
    "hightech_exports": {
        "label": "high-technology-export-share change",
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "sign": "+",
        "dims": ["industrial_capability", "trade_liberalisation"],
        "transformation": "2021-2023 mean minus 2006-2008 mean",
        "phrase": "a larger increase in high-technology exports as a manufacturing share",
        "mode": "change",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_frame(path: Path) -> pd.DataFrame:
    target = ROOT / path
    if not target.exists():
        raise FileNotFoundError(target)
    return pd.read_parquet(target)


def finite_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=columns).copy()
    return result


def configs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for treatment_id, treatment in MIN_WAGE_TREATMENTS.items():
        for outcome_id, outcome in MIN_WAGE_OUTCOMES.items():
            rows.append(
                {
                    "hypothesis_id": f"pcw100_us_mw_{treatment_id}_{outcome_id}",
                    "cohort": "us_minimum_wage",
                    "treatment_id": treatment_id,
                    "outcome_id": outcome_id,
                    "topic": outcome["topic"],
                    "expected_sign": outcome["sign"],
                    "period": [2006, 2024],
                    "min_observations": 100,
                    "min_units": 30,
                    "contrast_min": treatment["contrast_min"],
                }
            )
    for treatment_id, treatment in FISCAL_TREATMENTS.items():
        for outcome_id, outcome in FISCAL_OUTCOMES.items():
            rows.append(
                {
                    "hypothesis_id": f"pcw100_us_fiscal_{treatment_id}_{outcome_id}",
                    "cohort": "us_fiscal_policy",
                    "treatment_id": treatment_id,
                    "outcome_id": outcome_id,
                    "topic": outcome["topic"],
                    "expected_sign": treatment["signs"][outcome_id],
                    "period": [2017, 2022],
                    "min_observations": 120,
                    "min_units": 40,
                    "contrast_min": 0.5 if treatment_id != "debt_revenue_ratio" else 5.0,
                }
            )
    for treatment_id, treatment in EFW_TREATMENTS.items():
        for outcome_id, outcome in INTERNATIONAL_OUTCOMES.items():
            rows.append(
                {
                    "hypothesis_id": f"pcw100_global_efw_{treatment_id}_{outcome_id}",
                    "cohort": "international_policy",
                    "treatment_id": treatment_id,
                    "outcome_id": outcome_id,
                    "topic": treatment["topic"],
                    "expected_sign": outcome["sign"],
                    "period": [2006, 2023],
                    "min_observations": 35,
                    "min_units": 35,
                    "contrast_min": 0.5,
                }
            )
    ids = [row["hypothesis_id"] for row in rows]
    if len(rows) != 100 or len(set(ids)) != 100:
        raise AssertionError(f"wave must contain exactly 100 unique hypotheses, got {len(rows)}")
    return rows


def config_lookup() -> dict[str, dict[str, Any]]:
    return {row["hypothesis_id"]: row for row in configs()}


def min_wage_frame(config: dict[str, Any]) -> pd.DataFrame:
    treatment = MIN_WAGE_TREATMENTS[config["treatment_id"]]
    outcome = MIN_WAGE_OUTCOMES[config["outcome_id"]]
    mw = load_frame(STATE_MIN_WAGE)
    labor = load_frame(STATE_LABOR)
    mw = mw[mw["state_abbr"].isin(US_UNITS)].copy()
    labor = labor[labor["state_abbr"].isin(US_UNITS)].copy()
    keys = ["ieset_state_id", "state_abbr", "state_name", "year"]
    frame = mw.merge(labor, on=keys, how="left", suffixes=("", "_labor"))
    if outcome["column"] == "saipe_poverty_rate_all_ages":
        incidence = load_frame(STATE_INCIDENCE)
        incidence = incidence[incidence["state_abbr"].isin(US_UNITS)]
        frame = frame.merge(
            incidence[["state_abbr", "year", "saipe_poverty_rate_all_ages"]],
            on=["state_abbr", "year"],
            how="left",
        )
    frame = frame[(frame["year"] >= 2006) & (frame["year"] <= 2024)].copy()
    frame["binding_premium"] = (
        frame["effective_minimum_wage"] - frame["federal_minimum_wage"]
    ).clip(lower=0)
    frame["increase_event"] = (frame["minimum_wage_increase"] > 0.001).astype(float)
    frame = frame.sort_values(["state_abbr", "year"])
    source_col = outcome["column"]
    if config["outcome_id"] in {
        "median_wage_growth",
        "food_employment_growth",
        "food_establishment_growth",
    }:
        positive = frame[source_col].where(frame[source_col] > 0)
        frame["outcome"] = 100.0 * np.log(positive).groupby(frame["state_abbr"]).diff()
    elif config["outcome_id"] in {
        "median_wage",
        "p10_wage",
        "total_weekly_wage",
        "food_weekly_wage",
    }:
        frame["outcome"] = np.log(frame[source_col].where(frame[source_col] > 0))
    else:
        frame["outcome"] = frame[source_col]
    frame["treatment"] = frame[treatment["variable"]]
    return finite_frame(
        frame[["state_abbr", "state_name", "year", "treatment", "outcome"]],
        ["treatment", "outcome"],
    )


def fiscal_outcome_frame(outcome_id: str) -> pd.DataFrame:
    if outcome_id in {"poverty", "median_income"}:
        frame = load_frame(STATE_INCIDENCE)
        column = FISCAL_OUTCOMES[outcome_id]["column"]
        frame = frame[["state_abbr", "state_name", "year", column]].copy()
        if outcome_id == "median_income":
            frame["outcome"] = np.log(frame[column].where(frame[column] > 0))
        else:
            frame["outcome"] = frame[column]
        return frame[["state_abbr", "state_name", "year", "outcome"]]
    if outcome_id == "employment_ratio":
        frame = load_frame(STATE_LABOR)
        frame["outcome"] = frame["employment_population_ratio"]
        return frame[["state_abbr", "state_name", "year", "outcome"]]
    housing = load_frame(STATE_HOUSING)
    housing = housing.sort_values(["state_abbr", "year"]).copy()
    if outcome_id == "hpi_growth":
        positive = housing["fhfa_hpi_at_index"].where(housing["fhfa_hpi_at_index"] > 0)
        housing["outcome"] = 100.0 * np.log(positive).groupby(housing["state_abbr"]).diff()
        return housing[["state_abbr", "state_name", "year", "outcome"]]
    housing["outcome"] = np.log(
        housing["bps_total_permit_units"].where(
            housing["bps_total_permit_units"] > 0
        )
    )
    return housing[["state_abbr", "state_name", "year", "outcome"]]


def fiscal_frame(config: dict[str, Any]) -> pd.DataFrame:
    treatment = FISCAL_TREATMENTS[config["treatment_id"]]
    fiscal = load_frame(STATE_FISCAL)
    fiscal = fiscal[fiscal["state_abbr"].isin(US_UNITS)].copy()
    fiscal["treatment"] = (
        100.0 * fiscal[treatment["numerator"]] / fiscal["total_revenue"]
    )
    fiscal["outcome_year"] = fiscal["year"] + 1
    outcome = fiscal_outcome_frame(config["outcome_id"])
    outcome = outcome[outcome["state_abbr"].isin(US_UNITS)].copy()
    frame = fiscal.merge(
        outcome,
        left_on=["state_abbr", "outcome_year"],
        right_on=["state_abbr", "year"],
        how="left",
        suffixes=("", "_outcome"),
    )
    frame = frame.rename(columns={"year": "policy_year"})
    return finite_frame(
        frame[
            [
                "state_abbr",
                "state_name",
                "policy_year",
                "outcome_year",
                "treatment",
                "outcome",
            ]
        ],
        ["treatment", "outcome"],
    )


def country_window(frame: pd.DataFrame, start: int, end: int) -> pd.Series:
    subset = frame[(frame["year"] >= start) & (frame["year"] <= end)]
    return subset.groupby("country_iso3")["value"].mean()


def international_frame(config: dict[str, Any]) -> pd.DataFrame:
    treatment = load_frame(EFW_PATHS[config["treatment_id"]])
    treatment = treatment[(treatment["year"] >= 2006) & (treatment["year"] <= 2023)]
    treatment_mean = treatment.groupby("country_iso3")["value"].mean().rename("treatment")

    outcome_meta = INTERNATIONAL_OUTCOMES[config["outcome_id"]]
    outcome = load_frame(WDI_PATHS[config["outcome_id"]])
    outcome = outcome[(outcome["year"] >= 2006) & (outcome["year"] <= 2023)]
    baseline = country_window(outcome, 2006, 2008).rename("baseline_outcome")
    if outcome_meta["mode"] == "mean":
        outcome_value = (
            outcome.groupby("country_iso3")["value"].mean().rename("outcome")
        )
    else:
        endpoint = country_window(outcome, 2021, 2023)
        outcome_value = (endpoint - baseline).rename("outcome")

    gdp = load_frame(WDI_PATHS["gdp_pc_level"])
    gdp = gdp[(gdp["year"] >= 2006) & (gdp["year"] <= 2008)]
    gdp = gdp.groupby("country_iso3")["value"].mean()
    log_gdp = np.log(gdp.where(gdp > 0)).rename("log_initial_gdp_pc")

    frame = pd.concat(
        [treatment_mean, outcome_value, baseline, log_gdp], axis=1, join="inner"
    ).reset_index()
    return finite_frame(
        frame,
        ["treatment", "outcome", "baseline_outcome", "log_initial_gdp_pc"],
    )


def analysis_frame(config: dict[str, Any]) -> pd.DataFrame:
    if config["cohort"] == "us_minimum_wage":
        return min_wage_frame(config)
    if config["cohort"] == "us_fiscal_policy":
        return fiscal_frame(config)
    return international_frame(config)


def contrast_summary(config: dict[str, Any], frame: pd.DataFrame) -> dict[str, Any]:
    treatment = frame["treatment"].astype(float)
    if config["cohort"] == "us_minimum_wage" and config["treatment_id"] == "increase_event":
        low = frame[treatment == 0]
        high = frame[treatment == 1]
        return {
            "definition": "policy-event years versus non-event years",
            "low_value": 0.0,
            "high_value": 1.0,
            "gap": 1.0,
            "low_n": int(len(low)),
            "high_n": int(len(high)),
            "low_units": sorted(low["state_abbr"].unique().tolist()),
            "high_units": sorted(high["state_abbr"].unique().tolist()),
        }
    q25 = float(treatment.quantile(0.25))
    q75 = float(treatment.quantile(0.75))
    low = frame[treatment <= q25]
    high = frame[treatment >= q75]
    unit_col = "country_iso3" if config["cohort"] == "international_policy" else "state_abbr"
    return {
        "definition": "bottom treatment quartile versus top treatment quartile",
        "low_value": q25,
        "high_value": q75,
        "gap": q75 - q25,
        "low_n": int(len(low)),
        "high_n": int(len(high)),
        "low_units": sorted(low[unit_col].unique().tolist()),
        "high_units": sorted(high[unit_col].unique().tolist()),
    }


def preflight_one(config: dict[str, Any]) -> dict[str, Any]:
    frame = analysis_frame(config)
    unit_col = "country_iso3" if config["cohort"] == "international_policy" else "state_abbr"
    time_col = None
    if config["cohort"] == "us_minimum_wage":
        time_col = "year"
    elif config["cohort"] == "us_fiscal_policy":
        time_col = "policy_year"
    contrast = contrast_summary(config, frame)
    n_units = int(frame[unit_col].nunique())
    n_periods = int(frame[time_col].nunique()) if time_col else 1
    checks = {
        "min_observations": len(frame) >= config["min_observations"],
        "min_units": n_units >= config["min_units"],
        "treatment_varies": float(frame["treatment"].std()) > 0,
        "contrast_gap": contrast["gap"] >= config["contrast_min"],
        "contrast_groups": contrast["low_n"] >= 10 and contrast["high_n"] >= 10,
    }
    return {
        "hypothesis_id": config["hypothesis_id"],
        "cohort": config["cohort"],
        "n_observations": int(len(frame)),
        "n_units": n_units,
        "n_periods": n_periods,
        "treatment_sd": float(frame["treatment"].std()),
        "contrast": contrast,
        "checks": checks,
        "passed": all(checks.values()),
        "coefficient_estimated": False,
    }


def preflight_all() -> list[dict[str, Any]]:
    rows = [preflight_one(config) for config in configs()]
    failed = [row for row in rows if not row["passed"]]
    print(
        f"preflight: {len(rows) - len(failed)}/{len(rows)} pass "
        "(coverage and variation only; no coefficients estimated)"
    )
    for row in failed:
        failed_checks = [name for name, passed in row["checks"].items() if not passed]
        print(f"  FAIL {row['hypothesis_id']}: {', '.join(failed_checks)}")
    return rows


def variable_source(path: Path, publisher: str, series: str) -> dict[str, Any]:
    return {
        "name": series,
        "vintage_file": str(path),
        "publisher": publisher,
        "series_id": series,
        "sha256": sha256(ROOT / path),
        "source_url": f"derived://{path}" if str(path).startswith("data/derived/") else None,
    }


def input_vintages(config: dict[str, Any]) -> list[dict[str, Any]]:
    if config["cohort"] == "us_minimum_wage":
        paths = [
            (STATE_MIN_WAGE, "ieset_derived", "us_state_minimum_wage_treatment_panel"),
            (STATE_LABOR, "ieset_derived", "us_state_labor_outcome_panel"),
        ]
        if config["outcome_id"] == "poverty":
            paths.append(
                (STATE_INCIDENCE, "ieset_derived", "us_state_acs_saipe_incidence_panel")
            )
    elif config["cohort"] == "us_fiscal_policy":
        paths = [(STATE_FISCAL, "ieset_derived", "us_state_gov_finances_panel")]
        if config["outcome_id"] in {"poverty", "median_income"}:
            paths.append(
                (STATE_INCIDENCE, "ieset_derived", "us_state_acs_saipe_incidence_panel")
            )
        elif config["outcome_id"] == "employment_ratio":
            paths.append((STATE_LABOR, "ieset_derived", "us_state_labor_outcome_panel"))
        elif config["outcome_id"] == "permit_units":
            paths.append(
                (STATE_HOUSING, "ieset_derived", "us_state_housing_supply_price_panel")
            )
        else:
            paths.append(
                (STATE_HOUSING, "ieset_derived", "us_state_housing_supply_price_panel")
            )
    else:
        paths = [
            (
                EFW_PATHS[config["treatment_id"]],
                "fraser_efw",
                EFW_PATHS[config["treatment_id"]].name.split("@", 1)[0],
            ),
            (
                WDI_PATHS[config["outcome_id"]],
                "world_bank_wdi",
                WDI_PATHS[config["outcome_id"]].name.split("@", 1)[0],
            ),
            (
                WDI_PATHS["gdp_pc_level"],
                "world_bank_wdi",
                "NY.GDP.PCAP.KD",
            ),
        ]
    return [variable_source(*row) for row in paths]


def sign_word(sign: str) -> str:
    return "positive" if sign == "+" else "negative"


def state_min_wage_spec(config: dict[str, Any]) -> dict[str, Any]:
    treatment = MIN_WAGE_TREATMENTS[config["treatment_id"]]
    outcome = MIN_WAGE_OUTCOMES[config["outcome_id"]]
    hid = config["hypothesis_id"]
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": config["topic"],
        "claim_direction": config["expected_sign"],
        "claim": (
            f"Across the 50 US states and District of Columbia during 2006-2024, "
            f"higher {treatment['label']} predicts {outcome['phrase']} in a two-way "
            "state and year fixed-effects screen with state-clustered standard errors."
        ),
        "methodology_note": (
            "Registered as part of the 100-test policy-contrast wave. The design uses "
            "new state-level treatment and outcome panels, keeps null and contrary "
            "results, and is explicitly associational."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": ["USA"],
            "period": config["period"],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "retain the 50 states and District of Columbia; exclude US territories",
                "drop state-years missing the registered treatment or outcome",
                "do not impute treatment or outcome values",
            ],
        },
        "scope": {
            "period": config["period"],
            "countries": ["USA"],
            "outcome_dim": outcome["dims"],
            "policy_family": ["labour_market"],
            "treatment_tags": treatment["tags"],
        },
        "variables": {
            "outcome": [
                {
                    "name": config["outcome_id"],
                    "source": f"ieset_derived:{outcome['column']}",
                    "transformation": outcome["transformation"],
                    "notes": outcome["label"],
                }
            ],
            "treatment": [
                {
                    "name": config["treatment_id"],
                    "source": f"ieset_derived:{treatment['variable']}",
                    "transformation": treatment["transformation"],
                    "notes": treatment["label"],
                }
            ],
        },
        "intervention_channel": "regulatory",
        "intervention_channel_justification": (
            "State statutory wage floors are regulatory interventions; the design "
            "measures policy intensity rather than assigning ideological labels."
        ),
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["state", "year"],
            "clustering": "state",
            "notes": (
                "OLS with state and year indicators and state-clustered covariance. "
                "No coefficient is inspected before the specification commit."
            ),
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if the treatment coefficient is {sign_word(config['expected_sign'])} "
                f"with two-sided p<0.10. REFUTED if it is significantly opposite-signed "
                f"at p<0.10. Otherwise PARTIAL. A verdict requires at least "
                f"{config['min_observations']} observations, {config['min_units']} states, "
                f"and a registered contrast gap of at least {config['contrast_min']}; "
                "a failed data gate is INCONCLUSIVE rather than PARTIAL."
            ),
            "test": f"twoway_state_year_fe_{hid}",
            "threshold": {
                "expected_sign": config["expected_sign"],
                "p_max": P_MAX,
                "min_observations": config["min_observations"],
                "min_units": config["min_units"],
                "min_contrast_gap": config["contrast_min"],
            },
        },
        "prior_confidence": 0.55 if config["expected_sign"] == "+" else 0.52,
        "disclosure": (
            "Minimum-wage policy may respond to local labor conditions and may proxy "
            "for unmeasured state trends. The screen does not establish causality."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "notes": "Hypothesis-only research wave; no school-scoreboard linkage is asserted.",
    }


def state_fiscal_spec(config: dict[str, Any]) -> dict[str, Any]:
    treatment = FISCAL_TREATMENTS[config["treatment_id"]]
    outcome = FISCAL_OUTCOMES[config["outcome_id"]]
    hid = config["hypothesis_id"]
    direction_phrase = (
        outcome["positive"] if config["expected_sign"] == "+" else outcome["negative"]
    )
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": config["topic"],
        "claim_direction": config["expected_sign"],
        "claim": (
            f"Across the 50 US states and District of Columbia, higher "
            f"{treatment['label']} in fiscal years 2017-2021 predicts {direction_phrase} "
            "one year later in a state and policy-year fixed-effects screen."
        ),
        "methodology_note": (
            "Registered as part of the 100-test policy-contrast wave. The one-year "
            "ordering is fixed before estimation, all usable states are retained, and "
            "the claim remains associational because fiscal composition is endogenous."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": ["USA"],
            "period": config["period"],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "retain the 50 states and District of Columbia",
                "pair fiscal-year treatment t with outcome t+1",
                "drop rows with missing treatment denominator or registered outcome",
                "do not impute fiscal or outcome values",
            ],
        },
        "scope": {
            "period": config["period"],
            "countries": ["USA"],
            "outcome_dim": outcome["dims"],
            "policy_family": ["fiscal_policy", "tax_policy"],
            "treatment_tags": treatment["tags"],
        },
        "variables": {
            "outcome": [
                {
                    "name": config["outcome_id"],
                    "source": f"ieset_derived:{outcome['column']}",
                    "transformation": outcome["transformation"],
                    "notes": outcome["label"],
                }
            ],
            "treatment": [
                {
                    "name": config["treatment_id"],
                    "source": f"ieset_derived:{treatment['numerator']}",
                    "transformation": (
                        f"100 times {treatment['numerator']} divided by total_revenue"
                    ),
                    "notes": treatment["label"],
                }
            ],
        },
        "intervention_channel": "fiscal",
        "intervention_channel_justification": (
            "The treatment is a state fiscal-revenue or debt composition measure."
        ),
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["state", "policy_year"],
            "clustering": "state",
            "notes": (
                "OLS of next-year outcome on current fiscal composition with state and "
                "policy-year indicators and state-clustered covariance."
            ),
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if the treatment coefficient is {sign_word(config['expected_sign'])} "
                f"with two-sided p<0.10. REFUTED if it is significantly opposite-signed "
                f"at p<0.10. Otherwise PARTIAL. A verdict requires at least "
                f"{config['min_observations']} observations, {config['min_units']} states, "
                f"and a top-versus-bottom-quartile gap of at least {config['contrast_min']} "
                "ratio points; a failed data gate is INCONCLUSIVE."
            ),
            "test": f"lagged_state_policy_year_fe_{hid}",
            "threshold": {
                "expected_sign": config["expected_sign"],
                "p_max": P_MAX,
                "min_observations": config["min_observations"],
                "min_units": config["min_units"],
                "min_contrast_gap": config["contrast_min"],
            },
        },
        "prior_confidence": 0.50,
        "disclosure": (
            "State fiscal mixes reflect income, institutions, demographics, and policy "
            "needs. Favorable signs are screening evidence, not causal estimates."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "notes": "Hypothesis-only research wave; no school-scoreboard linkage is asserted.",
    }


def international_spec(config: dict[str, Any]) -> dict[str, Any]:
    treatment = EFW_TREATMENTS[config["treatment_id"]]
    outcome = INTERNATIONAL_OUTCOMES[config["outcome_id"]]
    hid = config["hypothesis_id"]
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "pre_registered",
        "topic": config["topic"],
        "claim_direction": config["expected_sign"],
        "claim": (
            f"Across countries covered by the pinned Fraser and World Bank panels "
            f"during 2006-2023, a higher average {treatment['label']} predicts "
            f"{outcome['phrase']} after conditioning on the baseline outcome and "
            "initial real GDP per capita."
        ),
        "methodology_note": (
            "Registered as part of the 100-test policy-contrast wave. The design "
            "compares top and bottom policy-regime quartiles over the past 18 years, "
            "uses HC3 covariance, retains null and contrary results, and is not causal."
        ),
        "evidence_type": "associational",
        "sample": {
            "countries": ["GLOBAL"],
            "period": config["period"],
            "temporal_structure": "cross_section_with_justification",
            "cross_section_justification": (
                "The estimand is a long-run policy-regime contrast: the 2006-2023 "
                "average treatment is related to a predeclared long-run outcome mean "
                "or endpoint-minus-baseline change."
            ),
            "exclusion_rules": [
                "retain country codes present in Fraser EFW and all registered WDI inputs",
                "require a finite baseline outcome and initial real GDP per capita",
                "do not impute treatment, outcome, or control values",
            ],
        },
        "scope": {
            "period": config["period"],
            "countries": ["GLOBAL"],
            "outcome_dim": outcome["dims"],
            "policy_family": treatment["policy_family"],
            "treatment_tags": treatment["tags"],
        },
        "variables": {
            "outcome": [
                {
                    "name": config["outcome_id"],
                    "source": outcome["source"],
                    "transformation": outcome["transformation"],
                    "notes": outcome["label"],
                }
            ],
            "treatment": [
                {
                    "name": config["treatment_id"],
                    "source": treatment["source"],
                    "transformation": "country mean over 2006-2023",
                    "notes": treatment["label"],
                }
            ],
            "controls": [
                {
                    "name": "baseline_outcome",
                    "source": outcome["source"],
                    "transformation": "country mean over 2006-2008",
                },
                {
                    "name": "log_initial_gdp_pc",
                    "source": "world_bank_wdi:NY.GDP.PCAP.KD",
                    "transformation": "log of 2006-2008 country mean",
                },
            ],
        },
        "intervention_channel": treatment["channel"],
        "intervention_channel_justification": (
            f"The {treatment['label']} is treated as a broad policy-regime proxy."
        ),
        "estimator": {
            "template": "descriptive",
            "clustering": "HC3 heteroskedasticity-robust covariance",
            "notes": (
                "Cross-country OLS of the registered long-run outcome on the average "
                "policy score, baseline outcome, and log initial real GDP per capita. "
                "The top/bottom quartile lists establish the substantive contrast."
            ),
        },
        "falsification": {
            "rule": (
                f"SUPPORTED if the treatment coefficient is {sign_word(config['expected_sign'])} "
                f"with two-sided HC3 p<0.10. REFUTED if it is significantly "
                f"opposite-signed at p<0.10. Otherwise PARTIAL. A verdict requires "
                f"at least {config['min_observations']} countries and a top-versus-bottom "
                f"quartile policy gap of at least {config['contrast_min']} EFW points; "
                "a failed data gate is INCONCLUSIVE."
            ),
            "test": f"long_run_policy_contrast_hc3_{hid}",
            "threshold": {
                "expected_sign": config["expected_sign"],
                "p_max": P_MAX,
                "min_observations": config["min_observations"],
                "min_units": config["min_units"],
                "min_contrast_gap": config["contrast_min"],
            },
        },
        "prior_confidence": treatment["prior"],
        "disclosure": (
            "Policy scores are endogenous to development, measurement quality varies, "
            "and omitted regional or historical factors may drive the association."
        ),
        "steelman": f"hypotheses/steelman/{hid}.md",
        "notes": "Hypothesis-only research wave; no school-scoreboard linkage is asserted.",
    }


def build_spec(config: dict[str, Any]) -> dict[str, Any]:
    if config["cohort"] == "us_minimum_wage":
        return state_min_wage_spec(config)
    if config["cohort"] == "us_fiscal_policy":
        return state_fiscal_spec(config)
    return international_spec(config)


def steelman_text(config: dict[str, Any]) -> str:
    hid = config["hypothesis_id"]
    if config["cohort"] == "us_minimum_wage":
        treatment = MIN_WAGE_TREATMENTS[config["treatment_id"]]["label"]
        outcome = MIN_WAGE_OUTCOMES[config["outcome_id"]]["label"]
        design = (
            "State and year effects absorb stable state differences and national shocks, "
            "but they do not absorb every state-specific trend or anticipation response."
        )
        mechanism = (
            "The strongest case is that a higher wage floor directly changes the price of "
            "low-wage labor, raising covered wages while potentially changing employment, "
            "entry, and poverty through income and substitution channels."
        )
    elif config["cohort"] == "us_fiscal_policy":
        treatment = FISCAL_TREATMENTS[config["treatment_id"]]["label"]
        outcome = FISCAL_OUTCOMES[config["outcome_id"]]["label"]
        design = (
            "One-year ordering prevents a purely contemporaneous outcome from defining the "
            "treatment, but fiscal choices still respond to anticipated conditions."
        )
        mechanism = (
            "The strongest case is that tax mix and debt burden change disposable income, "
            "public capacity, financing costs, and location incentives before the measured "
            "labor, distributional, or housing outcome."
        )
    else:
        treatment = EFW_TREATMENTS[config["treatment_id"]]["label"]
        outcome = INTERNATIONAL_OUTCOMES[config["outcome_id"]]["label"]
        design = (
            "Baseline controls and a long window reduce simple level confounding, but the "
            "cross-country comparison cannot isolate reform timing or eliminate reverse causality."
        )
        mechanism = (
            "The strongest case is that durable policy regimes affect contracting, price "
            "signals, investment horizons, market entry, and knowledge diffusion long enough "
            "to appear in the registered long-run outcome."
        )
    return f"""# Steelman — {hid}

## Strongest case for the claim

{mechanism}

The registered treatment is **{treatment}** and the registered outcome is
**{outcome}**. The top-versus-bottom contrast is reported even when the
regression is null or contrary.

## Strongest challenge

{design} Policy measurement may also proxy for income, administrative capacity,
political coalitions, demographics, or prior growth. These are credible rival
explanations, not after-the-fact exceptions.

## Interpretation discipline

This is an associational screen. A supported result clears the preregistered
directional hurdle but does not establish a causal effect. A significant
opposite sign is refuting evidence for this registered broad claim. An
insignificant estimate is PARTIAL, not evidence of no effect. Missing coverage
or an inadequate policy contrast is INCONCLUSIVE and does not graduate.
"""


def yaml_text(spec: dict[str, Any]) -> str:
    return (
        "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
        + yaml.safe_dump(spec, sort_keys=False, width=110, allow_unicode=False)
    )


def registry_markdown(rows: list[dict[str, Any]]) -> str:
    cohort_counts: dict[str, int] = {}
    for row in rows:
        cohort_counts[row["cohort"]] = cohort_counts.get(row["cohort"], 0) + 1
    lines = [
        "# Policy Contrast Wave 100 — preregistration registry",
        "",
        "- Wave date: 2026-07-18",
        f"- Hypotheses: {len(rows)}",
        "- Period constraint: every test is contained in 2006-2026",
        "- Coefficients inspected before registration: **none**",
        "- Decision rule: expected-sign p<0.10 = SUPPORTED; opposite-sign p<0.10 = REFUTED; otherwise PARTIAL",
        "- Data-gate failure: INCONCLUSIVE and not graduated",
        "",
        "## Cohorts",
        "",
    ]
    for cohort, count in sorted(cohort_counts.items()):
        lines.append(f"- `{cohort}`: {count}")
    lines.extend(
        [
            "",
            "## Registered tests",
            "",
            "| hypothesis | cohort | treatment | outcome | sign | n | units | contrast gap |",
            "| --- | --- | --- | --- | :---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        preflight = row["preflight"]
        lines.append(
            f"| `{row['hypothesis_id']}` | {row['cohort']} | {row['treatment_id']} | "
            f"{row['outcome_id']} | {row['expected_sign']} | "
            f"{preflight['n_observations']} | {preflight['n_units']} | "
            f"{preflight['contrast']['gap']:.4g} |"
        )
    return "\n".join(lines) + "\n"


def write_prereg() -> None:
    preflight = preflight_all()
    failed = [row for row in preflight if not row["passed"]]
    if failed:
        raise SystemExit("refusing to write preregistrations: preflight has failures")
    preflight_by_id = {row["hypothesis_id"]: row for row in preflight}
    rows = []
    for config in configs():
        hid = config["hypothesis_id"]
        spec = build_spec(config)
        spec_path = HYPOTHESES / config["topic"] / f"{hid}.yaml"
        steelman_path = STEELMEN / f"{hid}.md"
        run_dir = RUNS / hid
        if spec_path.exists() or steelman_path.exists() or run_dir.exists():
            raise SystemExit(f"refusing to overwrite existing wave artifact: {hid}")
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        STEELMEN.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(yaml_text(spec), encoding="utf-8")
        steelman_path.write_text(steelman_text(config), encoding="utf-8")
        row = dict(config)
        row["spec_path"] = rel(spec_path)
        row["steelman_path"] = rel(steelman_path)
        row["preflight"] = preflight_by_id[hid]
        row["input_vintages"] = input_vintages(config)
        rows.append(row)
    AUDITS.mkdir(parents=True, exist_ok=True)
    registry = {
        "wave_id": WAVE_ID,
        "registered_utc": utc_now(),
        "count": len(rows),
        "coefficient_estimated_during_preflight": False,
        "decision_rule": {
            "supported": "expected-sign coefficient with two-sided p<0.10",
            "refuted": "opposite-sign coefficient with two-sided p<0.10",
            "partial": "all other estimable results",
            "inconclusive": "any failed coverage, unit-count, variation, or contrast gate",
        },
        "hypotheses": rows,
    }
    REGISTRY_JSON.write_text(
        json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    REGISTRY_MD.write_text(registry_markdown(rows), encoding="utf-8")
    print(f"wrote {len(rows)} preregistrations and steelmen")
    print(f"registry: {rel(REGISTRY_JSON)}")


def gate_result(config: dict[str, Any], frame: pd.DataFrame) -> tuple[bool, dict[str, Any]]:
    preflight = preflight_one(config)
    return preflight["passed"], preflight


def estimate(config: dict[str, Any], frame: pd.DataFrame) -> dict[str, Any]:
    if config["cohort"] == "international_policy":
        model = smf.ols(
            "outcome ~ treatment + baseline_outcome + log_initial_gdp_pc",
            data=frame,
        ).fit(cov_type="HC3")
        method = "statsmodels OLS with HC3 covariance"
        r_squared = float(model.rsquared)
    else:
        time_col = "year" if config["cohort"] == "us_minimum_wage" else "policy_year"
        model = smf.ols(
            f"outcome ~ treatment + C(state_abbr) + C({time_col})",
            data=frame,
        ).fit(
            cov_type="cluster",
            cov_kwds={"groups": frame["state_abbr"], "use_correction": True},
        )
        method = "statsmodels OLS with state/year indicators and state-clustered covariance"
        r_squared = float(model.rsquared)
    coefficient = float(model.params["treatment"])
    standard_error = float(model.bse["treatment"])
    p_value = float(model.pvalues["treatment"])
    conf_int = model.conf_int().loc["treatment"]
    return {
        "coefficient": coefficient,
        "std_error": standard_error,
        "p_value": p_value,
        "conf_int_95": [float(conf_int.iloc[0]), float(conf_int.iloc[1])],
        "n_observations": int(model.nobs),
        "r_squared": r_squared,
        "method": method,
    }


def verdict(config: dict[str, Any], estimate_row: dict[str, Any]) -> tuple[str, str]:
    coefficient = estimate_row["coefficient"]
    p_value = estimate_row["p_value"]
    expected = config["expected_sign"]
    expected_match = coefficient > 0 if expected == "+" else coefficient < 0
    if p_value < P_MAX and expected_match:
        label = "SUPPORTED"
    elif p_value < P_MAX and not expected_match and coefficient != 0:
        label = "REFUTED"
    else:
        label = "PARTIAL"
    reason = (
        f"coefficient={coefficient:+.6g}, SE={estimate_row['std_error']:.6g}, "
        f"p={p_value:.6g}, expected_sign={expected}"
    )
    return label, reason


def result_card(
    config: dict[str, Any],
    label: str,
    reason: str,
    estimate_row: dict[str, Any] | None,
    preflight: dict[str, Any],
) -> str:
    lines = [
        f"# Result card — {config['hypothesis_id']}",
        "",
        f"- Verdict: **{label}**",
        f"- Cohort: `{config['cohort']}`",
        f"- Expected sign: `{config['expected_sign']}`",
        f"- Reason: {reason}",
        f"- Observations: {preflight['n_observations']}",
        f"- Units: {preflight['n_units']}",
        f"- Contrast: {preflight['contrast']['definition']}",
        f"- Contrast gap: {preflight['contrast']['gap']:.6g}",
        "",
        "## Extreme policy groups",
        "",
        f"- Low-policy units: {', '.join(preflight['contrast']['low_units'])}",
        f"- High-policy units: {', '.join(preflight['contrast']['high_units'])}",
        "",
        "## Registered decision rule",
        "",
        (
            "Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; "
            "significant opposite sign is REFUTED; all other estimable results "
            "are PARTIAL. A failed data gate is INCONCLUSIVE."
        ),
        "",
        "## Interpretation",
        "",
        (
            "This result is an associational screen. Fixed effects, temporal ordering, "
            "or baseline controls narrow some rival explanations but do not establish causality."
        ),
    ]
    if estimate_row:
        lines.extend(
            [
                "",
                "## Estimate",
                "",
                f"- Coefficient: {estimate_row['coefficient']:+.8g}",
                f"- Standard error: {estimate_row['std_error']:.8g}",
                f"- p-value: {estimate_row['p_value']:.8g}",
                f"- R-squared: {estimate_row['r_squared']:.6g}",
                f"- Method: {estimate_row['method']}",
            ]
        )
    return "\n".join(lines) + "\n"


def replication_text(hypothesis_id: str) -> str:
    return f"""#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
command = [
    sys.executable,
    str(root / "scripts" / "policy_contrast_wave_100.py"),
    "--run-one",
    "{hypothesis_id}",
    "--force",
]
raise SystemExit(subprocess.call(command, cwd=root))
"""


def run_one(hypothesis_id: str, force: bool = False) -> str:
    lookup = config_lookup()
    if hypothesis_id not in lookup:
        raise KeyError(f"unknown wave hypothesis: {hypothesis_id}")
    config = lookup[hypothesis_id]
    spec_path = HYPOTHESES / config["topic"] / f"{hypothesis_id}.yaml"
    if not spec_path.exists():
        raise FileNotFoundError(f"missing preregistration: {spec_path}")
    run_dir = RUNS / hypothesis_id
    if run_dir.exists() and not force:
        return f"SKIP {hypothesis_id}: run exists"
    run_dir.mkdir(parents=True, exist_ok=True)
    frame = analysis_frame(config)
    gate_passed, preflight = gate_result(config, frame)
    estimate_row: dict[str, Any] | None = None
    if gate_passed:
        estimate_row = estimate(config, frame)
        label, reason = verdict(config, estimate_row)
    else:
        label = "INCONCLUSIVE"
        failures = [name for name, passed in preflight["checks"].items() if not passed]
        reason = "failed registered data gate(s): " + ", ".join(failures)
    diagnostics = {
        "hypothesis_id": hypothesis_id,
        "wave_id": WAVE_ID,
        "cohort": config["cohort"],
        "verdict": label,
        "verdict_label": label,
        "verdict_reason": reason,
        "expected_sign": config["expected_sign"],
        "estimate": estimate_row,
        "preflight": preflight,
        "contrast": preflight["contrast"],
        "data_status": {
            "missing_series": [],
            "input_vintages": input_vintages(config),
        },
        "limitations": [
            "Associational design; the estimate is not a causal policy effect.",
            "The registered model does not eliminate all time-varying or cross-country confounding.",
        ],
        "run_utc": utc_now(),
        "runner": RUNNER_REL,
    }
    manifest = {
        "hypothesis_id": hypothesis_id,
        "wave_id": WAVE_ID,
        "runner": RUNNER_REL,
        "run_utc": diagnostics["run_utc"],
        "status": label,
        "vintages": input_vintages(config),
        "missing_series": [],
        "design": {
            "cohort": config["cohort"],
            "expected_sign": config["expected_sign"],
            "p_max": P_MAX,
            "contrast_definition": preflight["contrast"]["definition"],
        },
    }
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    (run_dir / "hypothesis.yaml").write_text(
        yaml.safe_dump(spec, sort_keys=False, width=110), encoding="utf-8"
    )
    (run_dir / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, width=110), encoding="utf-8"
    )
    (run_dir / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "result_card.md").write_text(
        result_card(config, label, reason, estimate_row, preflight), encoding="utf-8"
    )
    (run_dir / "replication.py").write_text(
        replication_text(hypothesis_id), encoding="utf-8"
    )
    coefficient_row = {
        "hypothesis_id": hypothesis_id,
        "verdict": label,
        "expected_sign": config["expected_sign"],
        "n_observations": preflight["n_observations"],
        "n_units": preflight["n_units"],
        "contrast_gap": preflight["contrast"]["gap"],
    }
    if estimate_row:
        coefficient_row.update(estimate_row)
    pd.DataFrame([coefficient_row]).to_parquet(
        run_dir / "coefficients.parquet", index=False
    )
    chart = {
        "hypothesis_id": hypothesis_id,
        "contrast": preflight["contrast"],
        "estimate": estimate_row,
        "verdict": label,
    }
    (run_dir / "chart_data.json").write_text(
        json.dumps(chart, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return f"{label} {hypothesis_id}: {reason}"


def run_all(force: bool = False) -> None:
    counts: dict[str, int] = {}
    for config in configs():
        message = run_one(config["hypothesis_id"], force=force)
        label = message.split(" ", 1)[0]
        counts[label] = counts.get(label, 0) + 1
        print(message)
    print("run summary:", json.dumps(counts, sort_keys=True))


def git_head() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def write_audit() -> None:
    prereg_path = ROOT / "engine" / "preregistration_index.json"
    prereg = (
        json.loads(prereg_path.read_text(encoding="utf-8"))
        if prereg_path.exists()
        else {"registrations": {}}
    )
    registrations = prereg.get("registrations", {})
    rows = []
    failures = []
    verdict_counts: dict[str, int] = {}
    cohort_counts: dict[str, int] = {}
    for config in configs():
        hid = config["hypothesis_id"]
        run_dir = RUNS / hid
        spec_path = HYPOTHESES / config["topic"] / f"{hid}.yaml"
        steelman_path = STEELMEN / f"{hid}.md"
        diagnostics_path = run_dir / "diagnostics.json"
        diagnostics = (
            json.loads(diagnostics_path.read_text(encoding="utf-8"))
            if diagnostics_path.exists()
            else {}
        )
        label = diagnostics.get("verdict_label", "MISSING")
        packet_path = run_dir / "evidence_packet.yaml"
        required = [
            run_dir / "hypothesis.yaml",
            run_dir / "manifest.yaml",
            diagnostics_path,
            run_dir / "result_card.md",
            run_dir / "replication.py",
            run_dir / "coefficients.parquet",
            run_dir / "chart_data.json",
            packet_path,
        ]
        checks = {
            "spec_exists": spec_path.exists(),
            "steelman_exists": steelman_path.exists(),
            "status_pre_registered": False,
            "strict_preregistration": registrations.get(hid, {}).get("status") == "verified",
            "definitive_verdict": label in {"SUPPORTED", "REFUTED", "PARTIAL"},
            "data_gate_passed": bool(diagnostics.get("preflight", {}).get("passed")),
            "all_run_artifacts": all(path.exists() for path in required),
            "replication_command": (run_dir / "replication.py").exists(),
            "provenance_hashes": False,
        }
        if spec_path.exists():
            spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            checks["status_pre_registered"] = spec.get("status") == "pre_registered"
        if packet_path.exists():
            packet = yaml.safe_load(packet_path.read_text(encoding="utf-8")) or {}
            inputs = packet.get("data", {}).get("inputs", [])
            checks["provenance_hashes"] = bool(inputs) and all(
                item.get("hash", {}).get("status") == "match" for item in inputs
            )
        passed = all(checks.values())
        if not passed:
            failures.append(
                {
                    "hypothesis_id": hid,
                    "failed_checks": [name for name, value in checks.items() if not value],
                }
            )
        verdict_counts[label] = verdict_counts.get(label, 0) + 1
        cohort_counts[config["cohort"]] = cohort_counts.get(config["cohort"], 0) + 1
        rows.append(
            {
                "hypothesis_id": hid,
                "cohort": config["cohort"],
                "verdict": label,
                "checks": checks,
                "graduated": passed,
                "estimate": diagnostics.get("estimate"),
                "contrast": diagnostics.get("contrast"),
            }
        )
    payload = {
        "wave_id": WAVE_ID,
        "generated_utc": utc_now(),
        "git_commit": git_head(),
        "hypothesis_count": len(rows),
        "graduated_count": sum(row["graduated"] for row in rows),
        "all_graduated": not failures and len(rows) == 100,
        "verdict_counts": verdict_counts,
        "cohort_counts": cohort_counts,
        "failures": failures,
        "hypotheses": rows,
    }
    AUDIT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Policy Contrast Wave 100 — graduation audit",
        "",
        f"- Hypotheses: {payload['hypothesis_count']}",
        f"- Graduated: {payload['graduated_count']}",
        f"- All graduated: **{payload['all_graduated']}**",
        f"- Verdicts: {json.dumps(verdict_counts, sort_keys=True)}",
        f"- Cohorts: {json.dumps(cohort_counts, sort_keys=True)}",
        "",
        "A hypothesis graduates only when its schema-valid preregistration and steelman "
        "exist, git history verifies strict preregistration, its registered data gate "
        "passes, its verdict is SUPPORTED/REFUTED/PARTIAL, every run artifact exists, "
        "and every input hash in the evidence packet matches.",
        "",
        "## Results",
        "",
        "| hypothesis | cohort | verdict | graduated |",
        "| --- | --- | --- | :---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['hypothesis_id']}` | {row['cohort']} | {row['verdict']} | "
            f"{'yes' if row['graduated'] else 'no'} |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        for failure in failures:
            lines.append(
                f"- `{failure['hypothesis_id']}`: {', '.join(failure['failed_checks'])}"
            )
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"graduation audit: {payload['graduated_count']}/{payload['hypothesis_count']} pass"
    )
    if failures:
        raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--write-prereg", action="store_true")
    group.add_argument("--run-all", action="store_true")
    group.add_argument("--run-one")
    group.add_argument("--write-audit", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        rows = preflight_all()
        return 0 if all(row["passed"] for row in rows) else 1
    if args.write_prereg:
        write_prereg()
        return 0
    if args.run_all:
        run_all(force=args.force)
        return 0
    if args.run_one:
        print(run_one(args.run_one, force=args.force))
        return 0
    write_audit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
