#!/usr/bin/env python3
"""Generate the first WDI/OWID structural verdict wave.

This is intentionally self-contained: it creates pre-registered descriptive
panel hypotheses plus the matching run artifacts without modifying shared
runners. The country-selection and grading thresholds are fixed in CASES below.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd
import pyarrow.parquet as pq
import yaml


ROOT = Path(__file__).resolve().parents[1]
WDI = ROOT / "data" / "vintages" / "world_bank_wdi"
OWID = ROOT / "data" / "vintages" / "owid"
RUNS = ROOT / "engine" / "runs"
STEEL = ROOT / "hypotheses" / "steelman"

AGGREGATE_ISO3 = {
    "AFE", "AFW", "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECS",
    "EMU", "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB", "IDX",
    "INX", "LAC", "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA", "MIC",
    "MNA", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS", "SSA", "SSF",
    "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "UMC", "WLD",
}


@dataclass(frozen=True)
class Case:
    hypothesis_id: str
    topic: str
    title: str
    claim: str
    period: tuple[int, int]
    sources: list[tuple[str, str]]
    treatment: list[dict]
    outcome: list[dict]
    row_builder: Callable[[], pd.DataFrame]
    pass_label: str
    pass_rate_support: float
    pass_rate_refute: float
    median_col: str
    median_support: float
    median_refute: float
    median_higher_is_better: bool
    min_n: int
    rule: str
    threshold: str
    prior: float
    disclosure: str
    outcome_dim: list[str]
    policy_family: list[str]
    tags: list[str]
    steelman: str


def latest(base: Path, series: str) -> Path:
    files = sorted(base.glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(series)
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wdi(series: str) -> pd.DataFrame:
    df = pq.read_table(latest(WDI, series)).to_pandas()
    df = df[df["country_iso3"].astype(str).str.match(r"^[A-Z]{3}$")].copy()
    df = df[~df["country_iso3"].isin(AGGREGATE_ISO3)].copy()
    return df[["country_iso3", "country_name", "year", "value"]].dropna()


def load_owid(series: str) -> pd.DataFrame:
    df = pq.read_table(latest(OWID, series)).to_pandas()
    meta = {"country_name", "country_iso3", "year", "World region according to OWID"}
    value_cols = [c for c in df.columns if c not in meta]
    if len(value_cols) != 1:
        raise ValueError(f"{series}: expected one value column, got {value_cols}")
    df = df[df["country_iso3"].astype(str).str.match(r"^[A-Z]{3}$")].copy()
    return (
        df[["country_iso3", "country_name", "year", value_cols[0]]]
        .rename(columns={value_cols[0]: "value"})
        .dropna()
    )


def endpoints(df: pd.DataFrame, y0: int, y1: int, min_obs: int) -> pd.DataFrame:
    rows = []
    for iso3, g in df[df["year"].between(y0, y1)].groupby("country_iso3"):
        g = g.sort_values("year")
        if len(g) < min_obs:
            continue
        rows.append(
            {
                "country_iso3": iso3,
                "country_name": str(g["country_name"].iloc[0]),
                "start_year": int(g["year"].iloc[0]),
                "start_value": float(g["value"].iloc[0]),
                "end_year": int(g["year"].iloc[-1]),
                "end_value": float(g["value"].iloc[-1]),
            }
        )
    return pd.DataFrame(rows)


def annual_mean(df: pd.DataFrame, y0: int, y1: int, min_obs: int, name: str) -> pd.DataFrame:
    sub = df[df["year"].between(y0, y1)].copy()
    out = (
        sub.groupby("country_iso3")
        .agg(country_name=("country_name", "first"), **{name: ("value", "mean")}, n_obs=("value", "count"))
        .reset_index()
    )
    return out[out["n_obs"] >= min_obs].drop(columns=["n_obs"])


def electrification_base() -> pd.DataFrame:
    elec = endpoints(load_wdi("EG.ELC.ACCS.ZS"), 1990, 2023, 15)
    elec["electricity_access_gain_pp"] = elec["end_value"] - elec["start_value"]
    return elec[elec["electricity_access_gain_pp"] >= 30.0][
        ["country_iso3", "country_name", "electricity_access_gain_pp"]
    ]


def build_electric_mortality() -> pd.DataFrame:
    mort = endpoints(load_wdi("SH.DYN.MORT"), 1990, 2023, 20)
    mort["under5_mortality_decline_pct"] = (mort["start_value"] - mort["end_value"]) / mort["start_value"] * 100.0
    rows = electrification_base().merge(mort[["country_iso3", "under5_mortality_decline_pct"]], on="country_iso3")
    rows["passes"] = rows["under5_mortality_decline_pct"] >= 50.0
    return rows.sort_values("country_iso3")


def build_electric_life() -> pd.DataFrame:
    life = endpoints(load_wdi("SP.DYN.LE00.IN"), 1990, 2023, 20)
    life["life_expectancy_gain_years"] = life["end_value"] - life["start_value"]
    rows = electrification_base().merge(life[["country_iso3", "life_expectancy_gain_years"]], on="country_iso3")
    rows["passes"] = rows["life_expectancy_gain_years"] >= 8.0
    return rows.sort_values("country_iso3")


def build_electric_growth() -> pd.DataFrame:
    growth = annual_mean(load_wdi("NY.GDP.PCAP.KD.ZG"), 1990, 2023, 20, "avg_real_gdp_pc_growth")
    rows = electrification_base().merge(growth[["country_iso3", "avg_real_gdp_pc_growth"]], on="country_iso3")
    rows["passes"] = rows["avg_real_gdp_pc_growth"] >= 1.0
    return rows.sort_values("country_iso3")


def remittance_base() -> pd.DataFrame:
    rem = annual_mean(load_wdi("BX.TRF.PWKR.DT.GD.ZS"), 2000, 2023, 10, "avg_remittances_pct_gdp")
    return rem[rem["avg_remittances_pct_gdp"] >= 8.0][
        ["country_iso3", "country_name", "avg_remittances_pct_gdp"]
    ]


def build_remittance_consumption() -> pd.DataFrame:
    cons = load_wdi("NE.CON.PRVT.KD.ZG")
    cons = cons[cons["year"].isin([2009, 2020, 2021])]
    shock = annual_mean(cons, 2009, 2021, 2, "avg_private_consumption_growth_shock_years")
    rows = remittance_base().merge(shock[["country_iso3", "avg_private_consumption_growth_shock_years"]], on="country_iso3")
    rows["passes"] = rows["avg_private_consumption_growth_shock_years"] >= 0.0
    return rows.sort_values("country_iso3")


def build_remittance_growth() -> pd.DataFrame:
    growth = load_wdi("NY.GDP.PCAP.KD.ZG")
    growth = growth[growth["year"].isin([2009, 2020, 2021])]
    shock = annual_mean(growth, 2009, 2021, 3, "avg_gdp_pc_growth_shock_years")
    rows = remittance_base().merge(shock[["country_iso3", "avg_gdp_pc_growth_shock_years"]], on="country_iso3")
    rows["passes"] = rows["avg_gdp_pc_growth_shock_years"] >= 0.0
    return rows.sort_values("country_iso3")


def build_remittance_current_account() -> pd.DataFrame:
    cab = annual_mean(load_wdi("BN.CAB.XOKA.GD.ZS"), 2000, 2023, 10, "avg_current_account_pct_gdp")
    rows = remittance_base().merge(cab[["country_iso3", "avg_current_account_pct_gdp"]], on="country_iso3")
    rows["passes"] = rows["avg_current_account_pct_gdp"] >= -10.0
    return rows.sort_values("country_iso3")


def tertiary_base() -> pd.DataFrame:
    ter = endpoints(load_wdi("SE.TER.CUAT.BA.ZS"), 2000, 2023, 8)
    ter["tertiary_attainment_gain_pp"] = ter["end_value"] - ter["start_value"]
    return ter[ter["tertiary_attainment_gain_pp"] >= 10.0][
        ["country_iso3", "country_name", "tertiary_attainment_gain_pp"]
    ]


def build_tertiary_services() -> pd.DataFrame:
    srv = endpoints(load_wdi("SL.SRV.EMPL.ZS"), 2000, 2023, 10)
    srv["services_employment_gain_pp"] = srv["end_value"] - srv["start_value"]
    rows = tertiary_base().merge(srv[["country_iso3", "services_employment_gain_pp"]], on="country_iso3")
    rows["passes"] = rows["services_employment_gain_pp"] >= 5.0
    return rows.sort_values("country_iso3")


def build_tertiary_productivity() -> pd.DataFrame:
    prod = endpoints(load_wdi("SL.GDP.PCAP.EM.KD"), 2000, 2023, 10)
    prod["labor_productivity_growth_pct"] = (prod["end_value"] / prod["start_value"] - 1.0) * 100.0
    rows = tertiary_base().merge(prod[["country_iso3", "labor_productivity_growth_pct"]], on="country_iso3")
    rows["passes"] = rows["labor_productivity_growth_pct"] >= 20.0
    return rows.sort_values("country_iso3")


def build_tertiary_growth() -> pd.DataFrame:
    growth = annual_mean(load_wdi("NY.GDP.PCAP.KD.ZG"), 2000, 2023, 15, "avg_real_gdp_pc_growth")
    rows = tertiary_base().merge(growth[["country_iso3", "avg_real_gdp_pc_growth"]], on="country_iso3")
    rows["passes"] = rows["avg_real_gdp_pc_growth"] >= 1.0
    return rows.sort_values("country_iso3")


def internet_base() -> pd.DataFrame:
    net = endpoints(load_owid("share-of-individuals-using-the-internet"), 2000, 2022, 10)
    net["internet_use_gain_pp"] = net["end_value"] - net["start_value"]
    return net[net["internet_use_gain_pp"] >= 40.0][
        ["country_iso3", "country_name", "internet_use_gain_pp"]
    ]


def build_internet_schooling() -> pd.DataFrame:
    school = endpoints(load_owid("mean-years-of-schooling-long-run"), 2000, 2020, 3)
    school["schooling_gain_years"] = school["end_value"] - school["start_value"]
    rows = internet_base().merge(school[["country_iso3", "schooling_gain_years"]], on="country_iso3")
    rows["passes"] = rows["schooling_gain_years"] >= 1.0
    return rows.sort_values("country_iso3")


def build_tax_child_mortality() -> pd.DataFrame:
    tax = endpoints(load_owid("tax-revenues-as-a-share-of-gdp"), 2000, 2022, 10)
    tax["tax_revenue_gain_pp"] = tax["end_value"] - tax["start_value"]
    cm = endpoints(load_owid("child-mortality-around-the-world"), 2000, 2022, 15)
    cm["child_mortality_decline_pct"] = (cm["start_value"] - cm["end_value"]) / cm["start_value"] * 100.0
    rows = tax[tax["tax_revenue_gain_pp"] >= 3.0][["country_iso3", "country_name", "tax_revenue_gain_pp"]].merge(
        cm[["country_iso3", "child_mortality_decline_pct"]], on="country_iso3"
    )
    rows["passes"] = rows["child_mortality_decline_pct"] >= 30.0
    return rows.sort_values("country_iso3")


def sources(*pairs: tuple[str, str]) -> list[tuple[str, str]]:
    return list(pairs)


CASES = [
    Case(
        "wdi_electrification_under5_mortality_followthrough_1990_2023",
        "growth",
        "WDI electrification and under-5 mortality follow-through, 1990-2023",
        "Countries with large electricity-access gains from 1990 to 2023 should usually show large under-5 mortality reductions over the same development window.",
        (1990, 2023),
        sources(("world_bank_wdi", "EG.ELC.ACCS.ZS"), ("world_bank_wdi", "SH.DYN.MORT")),
        [{"name": "electricity_access_gain", "source": "world_bank_wdi:EG.ELC.ACCS.ZS", "transformation": "country selected if endpoint gain >= 30pp"}],
        [{"name": "under5_mortality_decline", "source": "world_bank_wdi:SH.DYN.MORT", "transformation": "endpoint percent decline"}],
        build_electric_mortality,
        "under-5 mortality decline >= 50%",
        0.70, 0.50, "under5_mortality_decline_pct", 60.0, 40.0, True, 40,
        "SUPPORTED if n>=40, at least 70% of selected countries reduce under-5 mortality by >=50%, and the median decline is >=60%. REFUTED if fewer than 50% pass or the median decline is <40%. Otherwise PARTIAL.",
        "n >= 40 AND pass_rate >= 0.70 AND median_under5_mortality_decline_pct >= 60",
        0.74,
        "The prior expects electrification to travel with broad development capacity, but the design is descriptive and cannot isolate grid access from vaccines, income, sanitation, or conflict.",
        ["life_expectancy_health"], ["industrial_policy", "none"], ["electrification", "human_development"],
        "Electrification can be a marker rather than a cause. Mortality may fall because of immunization, clean water, nutrition, conflict cessation, or measurement improvements that happen alongside electricity expansion.",
    ),
    Case(
        "wdi_electrification_life_expectancy_followthrough_1990_2023",
        "growth",
        "WDI electrification and life-expectancy follow-through, 1990-2023",
        "Countries with large electricity-access gains from 1990 to 2023 should usually record substantial gains in life expectancy over the same period.",
        (1990, 2023),
        sources(("world_bank_wdi", "EG.ELC.ACCS.ZS"), ("world_bank_wdi", "SP.DYN.LE00.IN")),
        [{"name": "electricity_access_gain", "source": "world_bank_wdi:EG.ELC.ACCS.ZS", "transformation": "country selected if endpoint gain >= 30pp"}],
        [{"name": "life_expectancy_gain", "source": "world_bank_wdi:SP.DYN.LE00.IN", "transformation": "endpoint year gain"}],
        build_electric_life,
        "life expectancy gain >= 8 years",
        0.65, 0.45, "life_expectancy_gain_years", 8.0, 5.0, True, 40,
        "SUPPORTED if n>=40, at least 65% of selected countries gain >=8 life-expectancy years, and the median gain is >=8 years. REFUTED if fewer than 45% pass or the median gain is <5 years. Otherwise PARTIAL.",
        "n >= 40 AND pass_rate >= 0.65 AND median_life_expectancy_gain_years >= 8",
        0.68,
        "The prior expects a positive development bundle, but AIDS, war, and ageing composition can break the link between access and life expectancy.",
        ["life_expectancy_health"], ["industrial_policy", "none"], ["electrification", "human_development"],
        "Life expectancy is affected by epidemics, civil conflict, demographic structure, and public-health policy. Electricity access can improve hospitals and households but may not overcome those shocks.",
    ),
    Case(
        "wdi_electrification_growth_nonpenalty_1990_2023",
        "growth",
        "WDI electrification and real GDP-per-capita growth non-penalty, 1990-2023",
        "Large electricity-access expansion from 1990 to 2023 should generally coincide with positive average real GDP-per-capita growth rather than being bought at the price of stagnation.",
        (1990, 2023),
        sources(("world_bank_wdi", "EG.ELC.ACCS.ZS"), ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")),
        [{"name": "electricity_access_gain", "source": "world_bank_wdi:EG.ELC.ACCS.ZS", "transformation": "country selected if endpoint gain >= 30pp"}],
        [{"name": "real_gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "transformation": "annual mean"}],
        build_electric_growth,
        "average real GDP-per-capita growth >= 1%",
        0.60, 0.45, "avg_real_gdp_pc_growth", 1.0, 0.0, True, 40,
        "SUPPORTED if n>=40, at least 60% of selected countries average >=1% real GDP-per-capita growth, and the median average is >=1%. REFUTED if fewer than 45% pass or the median is <0%. Otherwise PARTIAL.",
        "n >= 40 AND pass_rate >= 0.60 AND median_avg_real_gdp_pc_growth >= 1",
        0.64,
        "The prior expects access expansion to be pro-growth or at least compatible with growth, but the panel mixes reconstruction, commodity busts, and fragile states.",
        ["gdp_growth", "energy"], ["industrial_policy", "none"], ["electrification", "growth_nonpenalty"],
        "GDP growth may come from commodity prices, migration, tourism, aid, or post-conflict rebound rather than electrification. Conversely, countries can electrify during macro crises.",
    ),
    Case(
        "wdi_remittance_consumption_resilience_2009_2021",
        "growth",
        "WDI remittance dependence and private-consumption resilience, 2009/2020/2021",
        "High-remittance economies should often show non-negative average private-consumption growth across the global shock years 2009, 2020, and 2021.",
        (2000, 2023),
        sources(("world_bank_wdi", "BX.TRF.PWKR.DT.GD.ZS"), ("world_bank_wdi", "NE.CON.PRVT.KD.ZG")),
        [{"name": "remittances_pct_gdp", "source": "world_bank_wdi:BX.TRF.PWKR.DT.GD.ZS", "transformation": "country selected if 2000-2023 mean >= 8% of GDP"}],
        [{"name": "private_consumption_growth", "source": "world_bank_wdi:NE.CON.PRVT.KD.ZG", "transformation": "mean across 2009, 2020, 2021"}],
        build_remittance_consumption,
        "average private-consumption growth in shock years >= 0%",
        0.60, 0.45, "avg_private_consumption_growth_shock_years", 1.0, -1.0, True, 25,
        "SUPPORTED if n>=25, at least 60% of high-remittance economies have non-negative average private-consumption growth in shock years, and the median shock-year average is >=1%. REFUTED if fewer than 45% pass or the median is below -1%. Otherwise PARTIAL.",
        "n >= 25 AND pass_rate >= 0.60 AND median_avg_private_consumption_growth_shock_years >= 1",
        0.61,
        "The prior expects remittances to stabilize household demand, but diaspora income can also fall during global recessions and reporting quality differs across corridors.",
        ["gdp_growth", "demographics_migration"], ["none"], ["remittances", "consumption_resilience"],
        "Remittances are not randomized insurance. High-remittance economies may be small, aid-dependent, tourism-exposed, or conflict-affected, and private consumption is measured with substantial national-account uncertainty.",
    ),
    Case(
        "wdi_remittance_gdp_pc_resilience_2009_2021",
        "growth",
        "WDI remittance dependence and GDP-per-capita resilience, 2009/2020/2021",
        "High-remittance economies should more often than not avoid negative average real GDP-per-capita growth across the global shock years 2009, 2020, and 2021.",
        (2000, 2023),
        sources(("world_bank_wdi", "BX.TRF.PWKR.DT.GD.ZS"), ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")),
        [{"name": "remittances_pct_gdp", "source": "world_bank_wdi:BX.TRF.PWKR.DT.GD.ZS", "transformation": "country selected if 2000-2023 mean >= 8% of GDP"}],
        [{"name": "real_gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "transformation": "mean across 2009, 2020, 2021"}],
        build_remittance_growth,
        "average real GDP-per-capita growth in shock years >= 0%",
        0.50, 0.40, "avg_gdp_pc_growth_shock_years", 0.0, -2.0, True, 25,
        "SUPPORTED if n>=25, at least 50% of high-remittance economies have non-negative average GDP-per-capita growth in shock years, and the median is >=0%. REFUTED if fewer than 40% pass or the median is below -2%. Otherwise PARTIAL.",
        "n >= 25 AND pass_rate >= 0.50 AND median_avg_gdp_pc_growth_shock_years >= 0",
        0.53,
        "The prior is modest because remittances stabilize households more directly than aggregate GDP, especially when tourism, construction, or conflict dominate the cycle.",
        ["gdp_growth", "demographics_migration"], ["none"], ["remittances", "macro_resilience"],
        "A remittance cushion need not prevent GDP-per-capita contractions. Lockdowns, oil shocks, tourism stops, disasters, and exchange-rate crises can dominate aggregate output.",
    ),
    Case(
        "wdi_remittance_current_account_cushion_2000_2023",
        "trade",
        "WDI remittance dependence and current-account cushion, 2000-2023",
        "High-remittance economies should usually avoid extreme average current-account deficits over 2000-2023 because worker transfers directly finance external balances.",
        (2000, 2023),
        sources(("world_bank_wdi", "BX.TRF.PWKR.DT.GD.ZS"), ("world_bank_wdi", "BN.CAB.XOKA.GD.ZS")),
        [{"name": "remittances_pct_gdp", "source": "world_bank_wdi:BX.TRF.PWKR.DT.GD.ZS", "transformation": "country selected if 2000-2023 mean >= 8% of GDP"}],
        [{"name": "current_account_pct_gdp", "source": "world_bank_wdi:BN.CAB.XOKA.GD.ZS", "transformation": "2000-2023 annual mean"}],
        build_remittance_current_account,
        "average current account >= -10% of GDP",
        0.70, 0.50, "avg_current_account_pct_gdp", -7.0, -12.0, True, 25,
        "SUPPORTED if n>=25, at least 70% of high-remittance economies average no worse than -10% of GDP on the current account, and the median average is >=-7%. REFUTED if fewer than 50% pass or the median is below -12%. Otherwise PARTIAL.",
        "n >= 25 AND pass_rate >= 0.70 AND median_avg_current_account_pct_gdp >= -7",
        0.67,
        "The prior expects worker transfers to matter mechanically in external accounts, but import dependence, aid inflows, debt service, and tourism cycles can overwhelm them.",
        ["trade_liberalisation", "capital_flows"], ["none"], ["remittances", "current_account"],
        "Current-account balances include goods trade, services, income, aid, and debt-service flows. Remittances may finance high imports rather than reduce deficits.",
    ),
    Case(
        "wdi_tertiary_attainment_services_shift_2000_2023",
        "growth",
        "WDI tertiary attainment and services employment shift, 2000-2023",
        "Countries with large tertiary-attainment gains from 2000 to 2023 should usually show a visible shift of employment toward services.",
        (2000, 2023),
        sources(("world_bank_wdi", "SE.TER.CUAT.BA.ZS"), ("world_bank_wdi", "SL.SRV.EMPL.ZS")),
        [{"name": "tertiary_attainment_gain", "source": "world_bank_wdi:SE.TER.CUAT.BA.ZS", "transformation": "country selected if endpoint gain >= 10pp"}],
        [{"name": "services_employment_share", "source": "world_bank_wdi:SL.SRV.EMPL.ZS", "transformation": "endpoint percentage-point change"}],
        build_tertiary_services,
        "services employment share gain >= 5pp",
        0.70, 0.50, "services_employment_gain_pp", 7.0, 2.0, True, 15,
        "SUPPORTED if n>=15, at least 70% of large-tertiary-gain countries increase services employment share by >=5pp, and the median gain is >=7pp. REFUTED if fewer than 50% pass or the median gain is <2pp. Otherwise PARTIAL.",
        "n >= 15 AND pass_rate >= 0.70 AND median_services_employment_gain_pp >= 7",
        0.75,
        "The prior expects skill upgrading to pair with services expansion, but services shares also rise mechanically when agriculture shrinks or manufacturing weakens.",
        ["employment_labour", "productivity"], ["labour_market", "none"], ["tertiary_attainment", "services_shift"],
        "Tertiary expansion may follow, not cause, structural change. Services can expand because of deindustrialization, tourism, public employment, or informality rather than high-skill productivity.",
    ),
    Case(
        "wdi_tertiary_attainment_labor_productivity_2000_2023",
        "growth",
        "WDI tertiary attainment and output per worker, 2000-2023",
        "Countries with large tertiary-attainment gains from 2000 to 2023 should usually register sizable growth in output per worker.",
        (2000, 2023),
        sources(("world_bank_wdi", "SE.TER.CUAT.BA.ZS"), ("world_bank_wdi", "SL.GDP.PCAP.EM.KD")),
        [{"name": "tertiary_attainment_gain", "source": "world_bank_wdi:SE.TER.CUAT.BA.ZS", "transformation": "country selected if endpoint gain >= 10pp"}],
        [{"name": "output_per_worker", "source": "world_bank_wdi:SL.GDP.PCAP.EM.KD", "transformation": "endpoint percent growth"}],
        build_tertiary_productivity,
        "output per worker growth >= 20%",
        0.70, 0.50, "labor_productivity_growth_pct", 25.0, 5.0, True, 15,
        "SUPPORTED if n>=15, at least 70% of large-tertiary-gain countries increase output per worker by >=20%, and the median gain is >=25%. REFUTED if fewer than 50% pass or the median gain is <5%. Otherwise PARTIAL.",
        "n >= 15 AND pass_rate >= 0.70 AND median_labor_productivity_growth_pct >= 25",
        0.69,
        "The prior expects education deepening to travel with productivity, but causality can run through capital deepening, migration, institutions, and sector mix.",
        ["productivity"], ["labour_market", "none"], ["tertiary_attainment", "labor_productivity"],
        "Output per worker may rise because of capital intensity, resource booms, employment composition, or exchange-rate valuation rather than tertiary education. Degree quality also varies sharply.",
    ),
    Case(
        "wdi_tertiary_attainment_growth_nonpenalty_2000_2023",
        "growth",
        "WDI tertiary attainment and GDP-per-capita growth non-penalty, 2000-2023",
        "Large tertiary-attainment gains from 2000 to 2023 should generally be compatible with positive average real GDP-per-capita growth.",
        (2000, 2023),
        sources(("world_bank_wdi", "SE.TER.CUAT.BA.ZS"), ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")),
        [{"name": "tertiary_attainment_gain", "source": "world_bank_wdi:SE.TER.CUAT.BA.ZS", "transformation": "country selected if endpoint gain >= 10pp"}],
        [{"name": "real_gdp_pc_growth", "source": "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "transformation": "2000-2023 annual mean"}],
        build_tertiary_growth,
        "average real GDP-per-capita growth >= 1%",
        0.65, 0.45, "avg_real_gdp_pc_growth", 1.0, 0.0, True, 15,
        "SUPPORTED if n>=15, at least 65% of large-tertiary-gain countries average >=1% real GDP-per-capita growth, and the median is >=1%. REFUTED if fewer than 45% pass or the median is <0%. Otherwise PARTIAL.",
        "n >= 15 AND pass_rate >= 0.65 AND median_avg_real_gdp_pc_growth >= 1",
        0.66,
        "The prior expects human-capital expansion to be growth-compatible, but the sample includes mature economies, oil exporters, and crisis-hit states.",
        ["gdp_growth", "productivity"], ["labour_market", "none"], ["tertiary_attainment", "growth_nonpenalty"],
        "More tertiary attainment can coincide with credential inflation, graduate unemployment, or slow mature-economy growth. Average GDP growth is a broad macro outcome with many confounders.",
    ),
    Case(
        "owid_internet_schooling_followthrough_2000_2022",
        "institutional_quality",
        "OWID internet diffusion and schooling follow-through, 2000-2022",
        "Countries with very large internet-use diffusion after 2000 should usually also show gains in average years of schooling, consistent with broader public-goods and capability expansion.",
        (2000, 2022),
        sources(("owid", "share-of-individuals-using-the-internet"), ("owid", "mean-years-of-schooling-long-run")),
        [{"name": "internet_use_gain", "source": "owid:share-of-individuals-using-the-internet", "transformation": "country selected if endpoint gain >= 40pp"}],
        [{"name": "mean_years_schooling", "source": "owid:mean-years-of-schooling-long-run", "transformation": "endpoint years gained"}],
        build_internet_schooling,
        "average years of schooling gain >= 1 year",
        0.65, 0.45, "schooling_gain_years", 1.0, 0.25, True, 50,
        "SUPPORTED if n>=50, at least 65% of large-internet-gain countries add >=1 average year of schooling, and the median gain is >=1 year. REFUTED if fewer than 45% pass or the median gain is <0.25 years. Otherwise PARTIAL.",
        "n >= 50 AND pass_rate >= 0.65 AND median_schooling_gain_years >= 1",
        0.63,
        "The prior expects digital diffusion to correlate with institutional and educational capacity, but internet adoption can leapfrog formal schooling or arrive after schooling gains.",
        ["institutional_quality", "employment_labour"], ["institutional_reform", "none"], ["internet_diffusion", "schooling"],
        "Internet use and schooling may both be consequences of income growth and urbanization. Internet diffusion can be mobile-led and commercial, while schooling depends on older cohorts and public education systems.",
    ),
    Case(
        "owid_tax_capacity_child_mortality_followthrough_2000_2022",
        "institutional_quality",
        "OWID tax capacity and child-mortality follow-through, 2000-2022",
        "Countries that materially raise tax revenues as a share of GDP from 2000 to 2022 should usually also achieve large child-mortality reductions, consistent with state-capacity public-goods follow-through.",
        (2000, 2022),
        sources(("owid", "tax-revenues-as-a-share-of-gdp"), ("owid", "child-mortality-around-the-world")),
        [{"name": "tax_revenue_gain", "source": "owid:tax-revenues-as-a-share-of-gdp", "transformation": "country selected if endpoint gain >= 3pp of GDP"}],
        [{"name": "child_mortality_decline", "source": "owid:child-mortality-around-the-world", "transformation": "endpoint percent decline"}],
        build_tax_child_mortality,
        "child mortality decline >= 30%",
        0.75, 0.50, "child_mortality_decline_pct", 45.0, 20.0, True, 30,
        "SUPPORTED if n>=30, at least 75% of tax-gain countries reduce child mortality by >=30%, and the median decline is >=45%. REFUTED if fewer than 50% pass or the median decline is <20%. Otherwise PARTIAL.",
        "n >= 30 AND pass_rate >= 0.75 AND median_child_mortality_decline_pct >= 45",
        0.72,
        "The prior expects fiscal capacity to correlate with public-goods delivery, but health gains may reflect vaccines, donors, income, or international diffusion rather than domestic tax revenue.",
        ["institutional_quality", "life_expectancy_health", "taxation"], ["tax_policy", "institutional_reform"], ["tax_capacity", "child_mortality"],
        "Tax-to-GDP can rise because of commodity cycles, formalization, or denominator effects. Child mortality may fall because of cheap global medical technology and donor programs even without stronger domestic tax capacity.",
    ),
]


def verdict(case: Case, rows: pd.DataFrame) -> tuple[str, str, dict]:
    n = len(rows)
    pass_rate = float(rows["passes"].mean()) if n else 0.0
    passed = int(rows["passes"].sum()) if n else 0
    median = float(rows[case.median_col].median()) if n else float("nan")
    median_support_ok = median >= case.median_support if case.median_higher_is_better else median <= case.median_support
    median_refute_hit = median < case.median_refute if case.median_higher_is_better else median > case.median_refute
    if n >= case.min_n and pass_rate >= case.pass_rate_support and median_support_ok:
        v = "supported"
    elif pass_rate < case.pass_rate_refute or median_refute_hit:
        v = "refuted"
    else:
        v = "partial"
    reason = f"{passed} of {n} countries passed ({pass_rate:.1%}); median {case.median_col} = {median:.2f}"
    metrics = {
        "n_countries": n,
        "countries_passing": passed,
        "pass_rate": pass_rate,
        f"median_{case.median_col}": median,
    }
    return v, reason, metrics


def write_hypothesis(case: Case, rows: pd.DataFrame) -> None:
    out_dir = ROOT / "hypotheses" / case.topic
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "hypothesis_id": case.hypothesis_id,
        "version": 1,
        "status": "pre_registered",
        "topic": case.topic,
        "claim": case.claim,
        "evidence_type": "descriptive",
        "sample": {
            "countries": sorted(rows["country_iso3"].unique().tolist()),
            "period": list(case.period),
            "temporal_structure": "panel",
        },
        "variables": {"outcome": case.outcome, "treatment": case.treatment},
        "estimator": {
            "template": "descriptive",
            "clustering": "none",
            "notes": "Custom endpoint/mean panel replication using local WDI/OWID vintages and fixed country-selection thresholds.",
        },
        "falsification": {"rule": case.rule, "test": case.hypothesis_id, "threshold": case.threshold},
        "prior_confidence": case.prior,
        "disclosure": case.disclosure,
        "steelman": f"hypotheses/steelman/{case.hypothesis_id}.md",
        "scope": {
            "period": list(case.period),
            "countries": sorted(rows["country_iso3"].unique().tolist()),
            "outcome_dim": case.outcome_dim,
            "policy_family": case.policy_family,
            "treatment_tags": case.tags,
        },
    }
    text = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
    text += yaml.safe_dump(doc, sort_keys=False, width=88)
    (out_dir / f"{case.hypothesis_id}.yaml").write_text(text)


def write_run(case: Case, rows: pd.DataFrame) -> None:
    out = RUNS / case.hypothesis_id
    out.mkdir(parents=True, exist_ok=True)
    v, reason, metrics = verdict(case, rows)
    rows.to_parquet(out / "coefficients.parquet", index=False)
    rows.to_json(out / "chart_data.json", orient="records", indent=2)
    paths = {
        f"{pub}:{series}": latest(WDI if pub == "world_bank_wdi" else OWID, series)
        for pub, series in case.sources
    }
    diag = {
        "hypothesis_id": case.hypothesis_id,
        "verdict": v,
        "reason": reason,
        "threshold": case.threshold,
        "metrics": metrics,
        "pass_label": case.pass_label,
        "countries": rows.to_dict(orient="records"),
        "vintages": {k: str(p.relative_to(ROOT)) for k, p in paths.items()},
        "sha256": {k: sha256(p) for k, p in paths.items()},
    }
    (out / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (out / "manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "hypothesis_id": case.hypothesis_id,
                "status": v,
                "reason": reason,
                "vintages": {k: str(p.relative_to(ROOT)) for k, p in paths.items()},
            },
            sort_keys=False,
        )
    )
    table_cols = [c for c in rows.columns if c != "passes"]
    header = "| " + " | ".join(table_cols + ["pass"]) + " |"
    sep = "|" + "|".join(["---"] * (len(table_cols) + 1)) + "|"
    body = "\n".join(
        "| "
        + " | ".join(
            [f"{r[c]:.2f}" if isinstance(r[c], float) else str(r[c]) for c in table_cols]
            + ["yes" if bool(r["passes"]) else "no"]
        )
        + " |"
        for _, r in rows.iterrows()
    )
    metric_lines = "\n".join(f"- {k}: {val}" for k, val in metrics.items())
    card = f"""# Result card - {case.hypothesis_id}

**Verdict:** {v} - {reason}

## Predeclared Threshold

{case.rule}

Threshold expression: `{case.threshold}`

## Metrics

{metric_lines}

## Country Panel

{header}
{sep}
{body}

## Interpretation

This is a descriptive structural-screen verdict using local WDI/OWID vintages.
It grades the predeclared pattern, not a causal effect of a single policy lever.

## Steelman

See `hypotheses/steelman/{case.hypothesis_id}.md`.
"""
    (out / "result_card.md").write_text(card)
    (out / "replication.py").write_text(
        "#!/usr/bin/env python3\n"
        '"""Regenerate this structural-wave artifact."""\n'
        "from pathlib import Path\n"
        "import runpy\n\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "runpy.run_path(str(root / 'scripts' / 'generate_wdi_owid_structural_wave.py'), run_name='__main__')\n"
    )


def write_steelman(case: Case) -> None:
    STEEL.mkdir(parents=True, exist_ok=True)
    (STEEL / f"{case.hypothesis_id}.md").write_text(
        f"# Steelman: {case.title}\n\n{case.steelman}\n"
    )


def main() -> None:
    for case in CASES:
        rows = case.row_builder().reset_index(drop=True)
        write_hypothesis(case, rows)
        write_steelman(case)
        write_run(case, rows)
        v, reason, _metrics = verdict(case, rows)
        print(f"{case.hypothesis_id}: {v} - {reason}")


if __name__ == "__main__":
    main()
