#!/usr/bin/env python3
"""Promote and run 50 broad cross-school panel hypotheses in five batches.

This is a throughput runner, not a scoreboard mapper. It intentionally covers
many schools of thought while keeping every test simple: one treatment, one
outcome, a small control set, country/year fixed effects, and clustered
standard errors by country.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
VINTAGES = ROOT / "data" / "vintages"
HYPOTHESES = ROOT / "hypotheses"
STEELMEN = HYPOTHESES / "steelman"
RUNS = ROOT / "engine" / "runs"
AUDITS = ROOT / "engine" / "audits"
ISO3_COUNTRIES = {country.alpha_3 for country in pycountry.countries}
ISO3_COUNTRIES.add("XKX")

SOURCES = {
    "efw_summary": ("fraser_efw", "summary_index", "Economic freedom summary index"),
    "efw_regulation": ("fraser_efw", "regulation", "Fraser regulation freedom score"),
    "efw_trade": ("fraser_efw", "freedom_to_trade_internationally", "Fraser freedom to trade score"),
    "efw_sound_money": ("fraser_efw", "sound_money", "Fraser sound money score"),
    "efw_size_government": ("fraser_efw", "size_of_government", "Fraser smaller-government score"),
    "kaopen": ("chinn_ito", "kaopen_index_normalized", "Chinn-Ito capital-account openness"),
    "wgi_ge": ("wgi", "GE.EST", "WGI government effectiveness"),
    "wgi_rl": ("wgi", "RL.EST", "WGI rule of law"),
    "wgi_rq": ("wgi", "GOV_WGI_RQ.EST", "WGI regulatory quality"),
    "gdp_pc_growth": ("world_bank_wdi", "NY.GDP.PCAP.KD.ZG", "real GDP per-capita growth"),
    "private_investment": ("world_bank_wdi", "NE.GDI.FPRV.ZS", "private fixed investment share"),
    "employment": ("world_bank_wdi", "SL.EMP.TOTL.SP.ZS", "employment-to-population ratio"),
    "unemployment": ("world_bank_wdi", "SL.UEM.TOTL.ZS", "unemployment rate"),
    "inflation": ("world_bank_wdi", "FP.CPI.TOTL.ZG", "CPI inflation"),
    "high_tech_exports": ("world_bank_wdi", "TX.VAL.TECH.MF.ZS", "high-tech exports share"),
    "manufacturing_share": ("world_bank_wdi", "NV.IND.MANF.ZS", "manufacturing value-added share"),
    "fdi": ("world_bank_wdi", "BX.KLT.DINV.WD.GD.ZS", "FDI inflows share"),
    "private_credit": ("world_bank_wdi", "FS.AST.PRVT.GD.ZS", "private credit to GDP"),
    "gov_consumption": ("world_bank_wdi", "NE.CON.GOVT.ZS", "government consumption share"),
    "public_debt": ("world_bank_wdi", "GC.DOD.TOTL.GD.ZS", "central government debt share"),
    "fiscal_balance": ("world_bank_wdi", "GC.NLD.TOTL.GD.ZS", "government net lending/borrowing share"),
    "tax_revenue": ("world_bank_wdi", "GC.TAX.TOTL.GD.ZS", "tax revenue share"),
    "life_expectancy": ("world_bank_wdi", "SP.DYN.LE00.IN", "life expectancy"),
    "child_mortality": ("world_bank_wdi", "SH.DYN.MORT", "under-5 mortality"),
    "poverty": ("world_bank_wdi", "SI.POV.DDAY", "extreme poverty headcount"),
    "gini": ("world_bank_wdi", "SI.POV.GINI", "Gini index"),
    "tertiary": ("world_bank_wdi", "SE.TER.ENRR", "tertiary enrollment"),
    "electricity_access": ("world_bank_wdi", "EG.ELC.ACCS.ZS", "electricity access"),
    "renewable_electricity": ("world_bank_wdi", "EG.ELC.RNEW.ZS", "renewable electricity share"),
    "fossil_electricity": ("world_bank_wdi", "EG.ELC.FOSL.ZS", "fossil electricity share"),
    "energy_use_pc": ("world_bank_wdi", "EG.USE.PCAP.KG.OE", "energy use per capita"),
    "trade_open": ("world_bank_wdi", "NE.TRD.GNFS.ZS", "trade openness"),
}

ALLOWED_OUTCOME_DIM = {
    "gdp_growth", "labour_share", "wage_stagnation", "productivity", "inflation",
    "monetary_policy", "fiscal_policy", "poverty_inequality", "employment_labour",
    "welfare_state", "trade_liberalisation", "financial_crisis", "financialisation",
    "institutional_quality", "housing", "energy", "industrial_capability",
    "competition_concentration", "regulation_compliance_cost", "life_expectancy_health",
    "currency_purchasing_power", "capital_flows", "demographics_migration", "taxation",
}


def c(
    hid: str,
    batch: str,
    schools: list[str],
    topic: str,
    claim: str,
    treatment: str,
    outcome: str,
    direction: str,
    dims: list[str],
    policy: list[str],
    controls: list[str] | None = None,
    period: tuple[int, int] = (1990, 2023),
) -> dict:
    return {
        "hid": hid, "batch": batch, "schools": schools, "topic": topic, "claim": claim,
        "treatment": treatment, "outcome": outcome, "direction": direction,
        "dims": dims, "policy": policy, "controls": controls or ["gdp_pc_growth"], "period": period,
    }


CASES = [
    # Batch 01: market-liberal / Austrian / Chicago / Ordoliberal.
    c("cross_school_efw_growth_market_order_1990_2023", "01_market_order", ["austrian", "classical_liberal", "chicago_monetarism", "ordoliberal"], "growth", "Higher broad economic freedom predicts faster real GDP per-capita growth.", "efw_summary", "gdp_pc_growth", "+", ["gdp_growth", "institutional_quality"], ["institutional_reform", "regulation"], []),
    c("cross_school_efw_private_investment_market_order_1990_2023", "01_market_order", ["austrian", "classical_liberal", "ordoliberal"], "growth", "Higher broad economic freedom predicts higher private-investment shares.", "efw_summary", "private_investment", "+", ["gdp_growth", "capital_flows"], ["institutional_reform", "regulation"]),
    c("cross_school_regulation_employment_market_order_1990_2023", "01_market_order", ["classical_liberal", "chicago_monetarism", "ordoliberal"], "labour", "More flexible regulation predicts higher employment-to-population ratios.", "efw_regulation", "employment", "+", ["employment_labour", "regulation_compliance_cost"], ["regulation", "labour_market"]),
    c("cross_school_trade_freedom_hightech_exports_1990_2023", "01_market_order", ["classical_liberal", "developmentalism", "ordoliberal"], "trade", "Freedom to trade predicts higher high-tech export intensity.", "efw_trade", "high_tech_exports", "+", ["trade_liberalisation", "industrial_capability"], ["trade_policy", "industrial_policy"]),
    c("cross_school_sound_money_inflation_reduction_1990_2023", "01_market_order", ["austrian", "chicago_monetarism"], "monetary", "Sound-money institutions predict lower inflation.", "efw_sound_money", "inflation", "-", ["inflation", "currency_purchasing_power"], ["monetary_policy"]),
    c("cross_school_smaller_government_growth_1990_2023", "01_market_order", ["austrian", "classical_liberal", "chicago_monetarism"], "fiscal", "Smaller-government EFW scores predict faster GDP per-capita growth.", "efw_size_government", "gdp_pc_growth", "+", ["gdp_growth", "fiscal_policy"], ["fiscal_policy"]),
    c("cross_school_capital_openness_fdi_1990_2023", "01_market_order", ["austrian", "classical_liberal", "ordoliberal"], "trade", "Capital-account openness predicts higher FDI inflows.", "kaopen", "fdi", "+", ["capital_flows", "trade_liberalisation"], ["exchange_rate_regime", "trade_policy"]),
    c("cross_school_rule_of_law_private_credit_depth_1996_2023", "01_market_order", ["ordoliberal", "classical_liberal"], "institutional_quality", "Rule of law predicts deeper private credit intermediation.", "wgi_rl", "private_credit", "+", ["institutional_quality", "financialisation"], ["institutional_reform", "regulation"], period=(1996, 2023)),
    c("cross_school_regulatory_quality_private_investment_1996_2023", "01_market_order", ["ordoliberal", "empirical_pragmatist"], "institutional_quality", "Regulatory quality predicts higher private-investment shares.", "wgi_rq", "private_investment", "+", ["institutional_quality", "capital_flows"], ["institutional_reform", "regulation"], period=(1996, 2023)),
    c("cross_school_trade_openness_growth_1990_2023", "01_market_order", ["classical_liberal", "developmentalism"], "trade", "Trade openness predicts faster real GDP per-capita growth.", "trade_open", "gdp_pc_growth", "+", ["trade_liberalisation", "gdp_growth"], ["trade_policy"]),

    # Batch 02: Marxian / market-socialist / financialisation claims.
    c("cross_school_private_credit_manufacturing_financialisation_1990_2023", "02_socialist_financialisation", ["marxian", "market_socialist", "post_keynesian"], "growth", "Private-credit depth predicts manufacturing-share erosion, consistent with financialisation crowding out production.", "private_credit", "manufacturing_share", "-", ["financialisation", "industrial_capability"], ["monetary_policy", "regulation"]),
    c("cross_school_private_credit_gini_financialisation_1990_2023", "02_socialist_financialisation", ["marxian", "post_keynesian"], "distribution", "Private-credit depth predicts higher income inequality.", "private_credit", "gini", "+", ["financialisation", "poverty_inequality"], ["monetary_policy", "regulation"]),
    c("cross_school_private_credit_growth_financialisation_1990_2023", "02_socialist_financialisation", ["marxian", "post_keynesian"], "growth", "Private-credit depth does not reliably translate into faster GDP per-capita growth.", "private_credit", "gdp_pc_growth", "-", ["financialisation", "gdp_growth"], ["monetary_policy", "regulation"]),
    c("cross_school_gini_growth_underconsumption_1990_2023", "02_socialist_financialisation", ["marxian", "social_democratic"], "distribution", "Higher inequality predicts slower GDP per-capita growth.", "gini", "gdp_pc_growth", "-", ["poverty_inequality", "gdp_growth"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_gini_employment_underconsumption_1990_2023", "02_socialist_financialisation", ["marxian", "social_democratic"], "labour", "Higher inequality predicts weaker employment outcomes.", "gini", "employment", "-", ["poverty_inequality", "employment_labour"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_tax_revenue_gini_redistribution_1990_2023", "02_socialist_financialisation", ["social_democratic", "market_socialist"], "distribution", "Higher tax revenue shares predict lower inequality.", "tax_revenue", "gini", "-", ["taxation", "poverty_inequality"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_gov_consumption_child_mortality_social_provision_1990_2023", "02_socialist_financialisation", ["social_democratic", "market_socialist"], "healthcare", "Higher government-consumption shares predict lower child mortality.", "gov_consumption", "child_mortality", "-", ["fiscal_policy", "life_expectancy_health"], ["fiscal_policy", "welfare_architecture"]),
    c("cross_school_gov_consumption_life_expectancy_social_provision_1990_2023", "02_socialist_financialisation", ["social_democratic", "market_socialist"], "healthcare", "Higher government-consumption shares predict higher life expectancy.", "gov_consumption", "life_expectancy", "+", ["fiscal_policy", "life_expectancy_health"], ["fiscal_policy", "welfare_architecture"]),
    c("cross_school_public_debt_growth_drag_1990_2023", "02_socialist_financialisation", ["marxian", "mmt", "post_keynesian"], "fiscal", "Public debt is not necessarily growth-damaging in broad panels.", "public_debt", "gdp_pc_growth", "+", ["fiscal_policy", "gdp_growth"], ["fiscal_policy"]),
    c("cross_school_public_debt_inflation_mmt_1990_2023", "02_socialist_financialisation", ["mmt", "post_keynesian"], "fiscal", "Public debt does not mechanically predict higher inflation.", "public_debt", "inflation", "-", ["fiscal_policy", "inflation"], ["fiscal_policy", "monetary_policy"]),

    # Batch 03: Keynesian/MMT/social-democratic fiscal stabilisation.
    c("cross_school_gov_consumption_unemployment_stabiliser_1990_2023", "03_keynesian_social_dem", ["post_keynesian", "new_keynesian", "social_democratic"], "fiscal", "Higher government consumption predicts lower unemployment.", "gov_consumption", "unemployment", "-", ["fiscal_policy", "employment_labour"], ["fiscal_policy"]),
    c("cross_school_gov_consumption_growth_multiplier_1990_2023", "03_keynesian_social_dem", ["post_keynesian", "new_keynesian"], "fiscal", "Higher government consumption predicts faster GDP per-capita growth.", "gov_consumption", "gdp_pc_growth", "+", ["fiscal_policy", "gdp_growth"], ["fiscal_policy"]),
    c("cross_school_fiscal_balance_unemployment_austerity_1990_2023", "03_keynesian_social_dem", ["post_keynesian", "social_democratic"], "fiscal", "Stronger fiscal balances predict higher unemployment if austerity is contractionary.", "fiscal_balance", "unemployment", "+", ["fiscal_policy", "employment_labour"], ["fiscal_policy"]),
    c("cross_school_fiscal_balance_growth_austerity_1990_2023", "03_keynesian_social_dem", ["post_keynesian", "social_democratic"], "fiscal", "Stronger fiscal balances predict slower GDP growth if consolidation is contractionary.", "fiscal_balance", "gdp_pc_growth", "-", ["fiscal_policy", "gdp_growth"], ["fiscal_policy"]),
    c("cross_school_tax_revenue_life_expectancy_social_capacity_1990_2023", "03_keynesian_social_dem", ["social_democratic", "new_keynesian"], "healthcare", "Higher tax revenue shares predict higher life expectancy through public capacity.", "tax_revenue", "life_expectancy", "+", ["taxation", "life_expectancy_health"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_tax_revenue_child_mortality_social_capacity_1990_2023", "03_keynesian_social_dem", ["social_democratic", "new_keynesian"], "healthcare", "Higher tax revenue shares predict lower child mortality.", "tax_revenue", "child_mortality", "-", ["taxation", "life_expectancy_health"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_tax_revenue_poverty_reduction_1990_2023", "03_keynesian_social_dem", ["social_democratic", "market_socialist"], "distribution", "Higher tax revenue shares predict lower extreme poverty.", "tax_revenue", "poverty", "-", ["taxation", "poverty_inequality"], ["tax_policy", "welfare_architecture"]),
    c("cross_school_public_debt_unemployment_mmt_1990_2023", "03_keynesian_social_dem", ["mmt", "post_keynesian"], "fiscal", "Higher public debt is associated with lower unemployment if deficits accommodate demand.", "public_debt", "unemployment", "-", ["fiscal_policy", "employment_labour"], ["fiscal_policy"]),
    c("cross_school_gov_consumption_private_investment_crowding_1990_2023", "03_keynesian_social_dem", ["post_keynesian", "austrian"], "fiscal", "Higher government consumption predicts lower private investment if crowding out dominates.", "gov_consumption", "private_investment", "-", ["fiscal_policy", "capital_flows"], ["fiscal_policy"]),
    c("cross_school_fiscal_balance_private_investment_confidence_1990_2023", "03_keynesian_social_dem", ["ordoliberal", "post_keynesian"], "fiscal", "Stronger fiscal balances predict higher private investment if confidence effects dominate.", "fiscal_balance", "private_investment", "+", ["fiscal_policy", "capital_flows"], ["fiscal_policy"]),

    # Batch 04: developmentalist / institutional capacity.
    c("cross_school_government_effectiveness_hightech_developmental_1996_2023", "04_developmental_institutional", ["developmentalism", "ordoliberal", "empirical_pragmatist"], "growth", "Government effectiveness predicts higher high-tech export intensity.", "wgi_ge", "high_tech_exports", "+", ["institutional_quality", "industrial_capability"], ["institutional_reform", "industrial_policy"], period=(1996, 2023)),
    c("cross_school_government_effectiveness_manufacturing_developmental_1996_2023", "04_developmental_institutional", ["developmentalism", "empirical_pragmatist"], "growth", "Government effectiveness predicts higher manufacturing value-added share.", "wgi_ge", "manufacturing_share", "+", ["institutional_quality", "industrial_capability"], ["institutional_reform", "industrial_policy"], period=(1996, 2023)),
    c("cross_school_government_effectiveness_fdi_developmental_1996_2023", "04_developmental_institutional", ["developmentalism", "ordoliberal"], "trade", "Government effectiveness predicts higher FDI inflows.", "wgi_ge", "fdi", "+", ["institutional_quality", "capital_flows"], ["institutional_reform", "industrial_policy"], period=(1996, 2023)),
    c("cross_school_rule_of_law_hightech_institutional_1996_2023", "04_developmental_institutional", ["ordoliberal", "classical_liberal"], "institutional_quality", "Rule of law predicts higher high-tech export intensity.", "wgi_rl", "high_tech_exports", "+", ["institutional_quality", "industrial_capability"], ["institutional_reform"], period=(1996, 2023)),
    c("cross_school_regulatory_quality_employment_institutional_1996_2023", "04_developmental_institutional", ["ordoliberal", "empirical_pragmatist"], "labour", "Regulatory quality predicts higher employment.", "wgi_rq", "employment", "+", ["institutional_quality", "employment_labour"], ["institutional_reform", "regulation"], period=(1996, 2023)),
    c("cross_school_trade_openness_manufacturing_developmental_1990_2023", "04_developmental_institutional", ["developmentalism", "classical_liberal"], "trade", "Trade openness predicts higher manufacturing value-added share.", "trade_open", "manufacturing_share", "+", ["trade_liberalisation", "industrial_capability"], ["trade_policy", "industrial_policy"]),
    c("cross_school_fdi_hightech_developmental_1990_2023", "04_developmental_institutional", ["developmentalism", "empirical_pragmatist"], "trade", "FDI inflows predict higher high-tech export intensity.", "fdi", "high_tech_exports", "+", ["capital_flows", "industrial_capability"], ["trade_policy", "industrial_policy"]),
    c("cross_school_private_credit_hightech_developmental_1990_2023", "04_developmental_institutional", ["developmentalism", "post_keynesian"], "growth", "Private credit depth predicts higher high-tech export intensity.", "private_credit", "high_tech_exports", "+", ["financialisation", "industrial_capability"], ["industrial_policy", "regulation"]),
    c("cross_school_tertiary_hightech_human_capital_1990_2023", "04_developmental_institutional", ["developmentalism", "social_democratic"], "growth", "Tertiary enrollment predicts higher high-tech export intensity.", "tertiary", "high_tech_exports", "+", ["productivity", "industrial_capability"], ["industrial_policy", "welfare_architecture"]),
    c("cross_school_government_effectiveness_growth_developmental_1996_2023", "04_developmental_institutional", ["developmentalism", "ordoliberal"], "growth", "Government effectiveness predicts faster GDP per-capita growth.", "wgi_ge", "gdp_pc_growth", "+", ["institutional_quality", "gdp_growth"], ["institutional_reform"], period=(1996, 2023)),

    # Batch 05: eco-socialist / degrowth / energy.
    c("cross_school_renewables_life_expectancy_ecosocial_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "degrowth"], "energy", "Higher renewable-electricity shares predict higher life expectancy.", "renewable_electricity", "life_expectancy", "+", ["energy", "life_expectancy_health"], ["energy_policy"]),
    c("cross_school_renewables_child_mortality_ecosocial_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "degrowth"], "energy", "Higher renewable-electricity shares predict lower child mortality.", "renewable_electricity", "child_mortality", "-", ["energy", "life_expectancy_health"], ["energy_policy"]),
    c("cross_school_fossil_electricity_child_mortality_ecosocial_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "degrowth"], "energy", "Higher fossil-electricity shares predict worse child-mortality outcomes.", "fossil_electricity", "child_mortality", "+", ["energy", "life_expectancy_health"], ["energy_policy"]),
    c("cross_school_fossil_electricity_growth_development_tradeoff_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "developmentalism"], "energy", "Higher fossil-electricity shares predict faster GDP growth in development panels.", "fossil_electricity", "gdp_pc_growth", "+", ["energy", "gdp_growth"], ["energy_policy", "industrial_policy"]),
    c("cross_school_energy_use_life_expectancy_degrowth_threshold_1990_2023", "05_eco_degrowth_energy", ["degrowth", "eco_socialist"], "energy", "Higher energy use per capita predicts higher life expectancy.", "energy_use_pc", "life_expectancy", "+", ["energy", "life_expectancy_health"], ["energy_policy"]),
    c("cross_school_energy_use_growth_degrowth_tradeoff_1990_2023", "05_eco_degrowth_energy", ["degrowth", "eco_socialist"], "energy", "Higher energy use per capita predicts faster GDP growth.", "energy_use_pc", "gdp_pc_growth", "+", ["energy", "gdp_growth"], ["energy_policy"]),
    c("cross_school_electricity_access_child_mortality_1990_2023", "05_eco_degrowth_energy", ["developmentalism", "eco_socialist"], "energy", "Electricity access predicts lower child mortality.", "electricity_access", "child_mortality", "-", ["energy", "life_expectancy_health"], ["energy_policy", "industrial_policy"]),
    c("cross_school_electricity_access_growth_1990_2023", "05_eco_degrowth_energy", ["developmentalism", "classical_liberal"], "energy", "Electricity access predicts faster GDP per-capita growth.", "electricity_access", "gdp_pc_growth", "+", ["energy", "gdp_growth"], ["energy_policy", "industrial_policy"]),
    c("cross_school_renewables_growth_cost_tradeoff_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "classical_liberal"], "energy", "Higher renewable-electricity shares predict faster GDP per-capita growth.", "renewable_electricity", "gdp_pc_growth", "+", ["energy", "gdp_growth"], ["energy_policy"]),
    c("cross_school_fossil_electricity_life_expectancy_tradeoff_1990_2023", "05_eco_degrowth_energy", ["eco_socialist", "degrowth"], "energy", "Higher fossil-electricity shares predict lower life expectancy after controls.", "fossil_electricity", "life_expectancy", "-", ["energy", "life_expectancy_health"], ["energy_policy"]),
]


def latest(pub: str, stem: str) -> Path:
    files = sorted((VINTAGES / pub).glob(f"{stem}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"missing vintage {pub}:{stem}")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise_source(key: str) -> tuple[pd.DataFrame, dict]:
    pub, stem, label = SOURCES[key]
    path = latest(pub, stem)
    df = pd.read_parquet(path)
    cols = {c.lower(): c for c in df.columns}
    country_col = cols.get("country_iso3") or cols.get("ccode") or cols.get("country")
    if country_col is None:
        raise ValueError(f"{key} has no recognised country column")
    out = df[[country_col, cols["year"], cols["value"]]].copy()
    out.columns = ["country", "year", key]
    out["country"] = out["country"].astype(str).str.upper()
    out = out[out["country"].str.fullmatch(r"[A-Z]{3}")]
    out = out[out["country"].isin(ISO3_COUNTRIES)]
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out[key] = pd.to_numeric(out[key], errors="coerce")
    out = out.dropna(subset=["country", "year", key])
    out["year"] = out["year"].astype(int)
    out = out.groupby(["country", "year"], as_index=False)[key].mean()
    meta = {"publisher": pub, "series": stem, "label": label, "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    return out, meta


def load_panel(keys: list[str]) -> tuple[pd.DataFrame, dict]:
    panel = None
    manifest = {}
    for key in keys:
        frame, meta = normalise_source(key)
        manifest[key] = meta
        panel = frame if panel is None else panel.merge(frame, on=["country", "year"], how="outer")
    assert panel is not None
    return panel, manifest


def fit_case(case: dict) -> tuple[pd.DataFrame, dict, dict]:
    controls = [col for col in case["controls"] if col not in {case["treatment"], case["outcome"]}]
    keys = [case["treatment"], case["outcome"]] + controls
    panel, manifest = load_panel(sorted(set(keys)))
    start, end = case["period"]
    panel = panel[(panel["year"] >= start) & (panel["year"] <= end)].copy()
    cols = ["country", "year", case["treatment"], case["outcome"]] + controls
    d = panel[cols].replace([math.inf, -math.inf], np.nan).dropna().copy()
    for col in [case["treatment"], case["outcome"]] + controls:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    d = d.dropna(subset=[case["treatment"], case["outcome"]] + controls).copy()
    n_countries = int(d["country"].nunique())
    if len(d) < 250 or n_countries < 20:
        return d, {
            "hypothesis_id": case["hid"], "verdict_label": "INCONCLUSIVE_DATA_PENDING",
            "verdict_reason": f"coverage gate failed: N={len(d)}, countries={n_countries}",
            "n_observations": int(len(d)), "n_countries": n_countries,
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "school_focus": case["schools"], "batch": case["batch"],
        }, manifest
    rhs = [case["treatment"]] + controls
    quoted_treatment = f"Q('{case['treatment']}')"
    formula = f"Q('{case['outcome']}') ~ " + " + ".join(f"Q('{col}')" for col in rhs) + " + C(country) + C(year)"
    try:
        fit = smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
        beta = float(fit.params[quoted_treatment])
        p = float(fit.pvalues[quoted_treatment])
        se = float(fit.bse[quoted_treatment])
        ci_low, ci_high = [float(x) for x in fit.conf_int().loc[quoted_treatment].tolist()]
    except Exception as exc:
        return d, {
            "hypothesis_id": case["hid"], "verdict_label": "INCONCLUSIVE_DATA_PENDING",
            "verdict_reason": f"model fit failed: {type(exc).__name__}: {exc}",
            "n_observations": int(len(d)), "n_countries": n_countries,
            "formula": formula,
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "school_focus": case["schools"], "batch": case["batch"],
        }, manifest
    sign_ok = beta >= 0 if case["direction"] == "+" else beta <= 0
    if p <= 0.10 and sign_ok:
        verdict, reason = "SUPPORTED", "coefficient has the predeclared sign and p <= 0.10"
    elif p <= 0.10 and not sign_ok:
        verdict, reason = "REFUTED", "coefficient is statistically significant in the opposite direction"
    else:
        verdict, reason = "PARTIAL", "coefficient is not statistically decisive at p <= 0.10"
    return d, {
        "hypothesis_id": case["hid"],
        "verdict_label": verdict,
        "verdict_reason": reason,
        "n_observations": int(len(d)),
        "n_countries": n_countries,
        "formula": formula,
        "coefficient": beta,
        "standard_error_cluster_country": se,
        "p_value": p,
        "ci95": [ci_low, ci_high],
        "direction": case["direction"],
        "treatment": case["treatment"],
        "outcome": case["outcome"],
        "controls": controls,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "scripts/promote_cross_school_next50_2026_05_12.py",
        "school_focus": case["schools"],
        "batch": case["batch"],
    }, manifest


def write_outputs(case: dict, d: pd.DataFrame, diag: dict, manifest: dict) -> None:
    controls = [col for col in case["controls"] if col not in {case["treatment"], case["outcome"]}]
    topic_dir = HYPOTHESES / case["topic"]
    topic_dir.mkdir(parents=True, exist_ok=True)
    STEELMEN.mkdir(parents=True, exist_ok=True)
    run_dir = RUNS / case["hid"]
    run_dir.mkdir(parents=True, exist_ok=True)

    hyp = {
        "hypothesis_id": case["hid"],
        "version": 1,
        "status": "candidate",
        "topic": case["topic"],
        "claim": case["claim"],
        "covers_claims": [],
        "evidence_type": "associational",
        "sample": {
            "countries": sorted(d["country"].dropna().unique().tolist()) or ["USA"],
            "period": list(case["period"]),
            "temporal_structure": "panel",
            "exclusion_rules": ["drop rows missing treatment, outcome, or controls", "require at least 250 observations and 20 countries"],
        },
        "variables": {
            "outcome": [{"name": case["outcome"], "source": f"{manifest[case['outcome']]['publisher']}:{manifest[case['outcome']]['series']}", "transformation": "level"}],
            "treatment": [{"name": case["treatment"], "source": f"{manifest[case['treatment']]['publisher']}:{manifest[case['treatment']]['series']}", "transformation": "level"}],
            "controls": [{"name": key, "source": f"{manifest[key]['publisher']}:{manifest[key]['series']}", "transformation": "level"} for key in controls],
        },
        "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country"},
        "falsification": {
            "rule": f"Supported if the coefficient on {case['treatment']} has sign {case['direction']} and p <= 0.10; refuted if significant in the opposite direction.",
            "test": case["hid"],
            "threshold": f"sign({case['treatment']})={case['direction']} and p<=0.10",
        },
        "prior_confidence": 0.52,
        "disclosure": "Generated as part of a cross-school throughput wave. This is a broad panel association, not a structural causal estimate.",
        "steelman": f"hypotheses/steelman/{case['hid']}.md",
        "scope": {"period": list(case["period"]), "countries": ["GLOBAL"], "outcome_dim": [x for x in case["dims"] if x in ALLOWED_OUTCOME_DIM], "policy_family": case["policy"], "treatment_tags": [case["treatment"]]},
        "notes": f"School coverage focus: {', '.join(case['schools'])}. Generated and run by scripts/promote_cross_school_next50_2026_05_12.py.",
    }
    (topic_dir / f"{case['hid']}.yaml").write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" + yaml.safe_dump(hyp, sort_keys=False, allow_unicode=False))
    (STEELMEN / f"{case['hid']}.md").write_text(
        f"# Steelman - {case['hid']}\n\n"
        f"Claim tested: {case['claim']}\n\n"
        "The strongest skeptical reading is that broad country-panel associations can be confounded by income level, demography, geography, commodity cycles, or policy endogeneity. "
        "This wave is useful for screening whether the claim generalises, not for final causal identification.\n"
    )
    (run_dir / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": case["hid"],
        "run_utc": diag["run_utc"],
        "verdict_label": diag["verdict_label"],
        "vintages": manifest,
        "formula": diag.get("formula"),
    }, sort_keys=False))
    if "coefficient" in diag:
        pd.DataFrame([{"hypothesis_id": case["hid"], "term": case["treatment"], "estimate": diag["coefficient"], "std_error": diag["standard_error_cluster_country"], "p_value": diag["p_value"], "ci95_low": diag["ci95"][0], "ci95_high": diag["ci95"][1], "n_observations": diag["n_observations"], "n_countries": diag["n_countries"]}]).to_parquet(run_dir / "coefficients.parquet", index=False)
    chart = d.groupby("year", as_index=False)[case["outcome"]].mean().rename(columns={case["outcome"]: "mean_outcome"}).to_dict("records") if not d.empty else []
    (run_dir / "chart_data.json").write_text(json.dumps({"series": chart}, indent=2))
    (run_dir / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess, sys\nROOT = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(ROOT / 'scripts' / 'promote_cross_school_next50_2026_05_12.py'), '{case['hid']}']))\n"
    )
    card = f"""# Result card - {case['hid']}

**Verdict:** {diag['verdict_label']} - {diag['verdict_reason']}.

## Plain-English Claim

{case['claim']}

## School Coverage

{', '.join(case['schools'])}

## What Was Measured

- Outcome: `{case['outcome']}`.
- Treatment: `{case['treatment']}`.
- Controls: {', '.join(f'`{x}`' for x in controls) if controls else 'none'}.

## Results

- Usable panel: **{diag['n_observations']:,} observations**, **{diag['n_countries']} countries**.
"""
    if "coefficient" in diag:
        card += f"- Coefficient on treatment: **{diag['coefficient']:.4f}** (SE {diag['standard_error_cluster_country']:.4f}, p={diag['p_value']:.4f}).\n"
        card += f"\n## Specification\n\n`{diag['formula']}`\n"
    card += "\nThis is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.\n"
    (run_dir / "result_card.md").write_text(card)


def run_targets(targets: list[str]) -> list[dict]:
    by_id = {case["hid"]: case for case in CASES}
    selected = [by_id[t] for t in targets] if targets else CASES
    results = []
    for case in selected:
        d, diag, manifest = fit_case(case)
        write_outputs(case, d, diag, manifest)
        results.append({"hypothesis_id": case["hid"], "batch": case["batch"], "schools": case["schools"], "verdict": diag["verdict_label"], "reason": diag["verdict_reason"]})
    return results


def write_audit(results: list[dict]) -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    verdicts = Counter(r["verdict"] for r in results)
    by_batch = defaultdict(Counter)
    by_school = defaultdict(Counter)
    for r in results:
        by_batch[r["batch"]][r["verdict"]] += 1
        for school in r["schools"]:
            by_school[school][r["verdict"]] += 1
    lines = ["# Cross-School Next 50 Results - 2026-05-12", "", "## Verdict Tally", ""]
    for k, v in sorted(verdicts.items()):
        lines.append(f"- `{k}`: {v}")
    lines += ["", "## By Batch", ""]
    for batch in sorted(by_batch):
        lines.append(f"- `{batch}`: {dict(by_batch[batch])}")
    lines += ["", "## By School Focus", ""]
    for school in sorted(by_school):
        lines.append(f"- `{school}`: {dict(by_school[school])}")
    lines += ["", "## Results", "", "| Hypothesis | Batch | Schools | Verdict |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| `{r['hypothesis_id']}` | `{r['batch']}` | {', '.join(r['schools'])} | `{r['verdict']}` |")
    (AUDITS / "cross_school_next50_results_2026-05-12.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str]) -> int:
    targets = argv[1:]
    results = run_targets(targets)
    if not targets:
        write_audit(results)
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
