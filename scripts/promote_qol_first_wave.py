#!/usr/bin/env python3
"""Promote a first wave from the 200 long-horizon QOL backlog.

These specs are deliberately local-data first-pass screens. They use WDI, WGI,
BIS, and PWT-style variables already used elsewhere in the repo. The goal is to
turn the prose backlog into runnable IDs, then separate real verdicts from data
blockers.
"""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = [
    "USA", "GBR", "CAN", "AUS", "NZL", "DEU", "FRA", "ITA", "ESP", "NLD",
    "SWE", "NOR", "DNK", "FIN", "JPN", "KOR", "CHN", "IND", "BRA", "MEX",
    "CHL", "ARG", "TUR", "ZAF", "POL", "EST", "VNM", "THA", "MYS", "IDN",
    "COL", "PER", "PHL", "EGY", "MAR", "KEN", "NGA", "BGD", "PAK", "LKA",
]


CASES = [
    ("growth", "market_openness_multidimensional_prosperity_1995_2024", "Higher trade and investment openness predicts stronger long-run prosperity gains.", "world_bank_wdi:NY.GDP.PCAP.KD", "world_bank_wdi:NE.TRD.GNFS.ZS", [1995, 2023], ["gdp_growth", "qol"], ["trade_policy", "competition_policy"], ["trade_openness", "market_openness"]),
    ("growth", "middle_income_qol_market_transition_1980_2024", "Middle-income countries that liberalize product and trade markets show stronger long-run income gains.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "world_bank_wdi:NE.TRD.GNFS.ZS", [1980, 2023], ["gdp_growth", "qol"], ["trade_policy", "regulation"], ["middle_income_transition", "trade_openness"]),
    ("institutional_quality", "intervention_qol_corruption_interaction", "Where corruption control is weak, heavier state intervention predicts weaker quality-of-life gains.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "wgi:CC.EST", [1996, 2023], ["gdp_growth", "institutional_quality"], ["institutional_reform", "fiscal_policy"], ["corruption_control", "state_intervention"]),
    ("institutional_quality", "market_institutions_qol_crisis_recovery", "Countries with stronger market-compatible institutions recover prosperity losses faster after shocks.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "wgi:RQ.EST", [1996, 2023], ["gdp_growth", "institutional_quality"], ["regulation", "institutional_reform"], ["regulatory_quality", "crisis_recovery"]),
    ("regulatory", "price_signal_integrity_qol_panel", "Lower price-distortion intensity predicts stronger long-run goods availability and living-standard gains.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RQ.EST", [1996, 2023], ["welfare_state", "productivity"], ["regulation"], ["price_signal_integrity", "regulatory_quality"]),
    ("growth", "market_institution_duration_qol_persistence", "Longer continuous duration of market-compatible institutions predicts higher quality-of-life levels.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RQ.EST", [1996, 2023], ["welfare_state", "gdp_growth"], ["institutional_reform", "regulation"], ["institution_duration", "regulatory_quality"]),
    ("growth", "trade_openness_consumer_welfare_1980_2024", "Trade openness predicts higher real household consumption over long windows.", "world_bank_wdi:NE.CON.PRVT.PC.KD", "world_bank_wdi:NE.TRD.GNFS.ZS", [1980, 2023], ["gdp_growth", "trade_liberalisation"], ["trade_policy"], ["trade_openness", "consumer_welfare"]),
    ("regulatory", "market_opening_durable_goods_diffusion", "Market opening predicts faster diffusion of consumer durable and communications technologies.", "world_bank_wdi:IT.NET.USER.ZS", "world_bank_wdi:NE.TRD.GNFS.ZS", [1990, 2023], ["welfare_state", "productivity"], ["trade_policy", "competition_policy"], ["market_opening", "technology_diffusion"]),
    ("fiscal", "interventionist_subsidy_consumption_decay", "Persistent broad subsidy and government-consumption burdens predict weaker long-run household consumption growth.", "world_bank_wdi:NE.CON.PRVT.PC.KD", "world_bank_wdi:NE.CON.GOVT.ZS", [1980, 2023], ["gdp_growth", "fiscal_policy"], ["fiscal_policy"], ["government_consumption", "subsidy_burden"]),
    ("fiscal", "tax_simplicity_disposable_income_growth", "Higher broad tax burden proxies predict slower disposable-income and consumption growth.", "world_bank_wdi:NE.CON.PRVT.PC.KD", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", [1990, 2023], ["gdp_growth", "taxation"], ["tax_policy"], ["tax_burden", "tax_simplicity"]),
    ("growth", "market_reform_inflation_adjusted_wages", "Market reforms predict stronger long-run real wage proxies through productivity and income growth.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RQ.EST", [1996, 2023], ["wage_stagnation", "gdp_growth"], ["regulation", "institutional_reform"], ["market_reform", "real_wages"]),
    ("healthcare", "market_freedom_life_expectancy_1970_2024", "Market-compatible institutions predict higher life expectancy after controlling for income.", "world_bank_wdi:SP.DYN.LE00.IN", "wgi:RQ.EST", [1996, 2023], ["life_expectancy_health"], ["regulation", "institutional_reform"], ["market_freedom", "life_expectancy"]),
    ("healthcare", "property_rights_child_mortality_decline", "Stronger rule of law and property rights predict lower child mortality over long windows.", "world_bank_wdi:SH.DYN.MORT", "wgi:RL.EST", [1996, 2023], ["life_expectancy_health"], ["institutional_reform"], ["property_rights", "child_mortality"]),
    ("healthcare", "trade_openness_medicine_access", "Trade openness predicts better access to medical capacity and health inputs.", "world_bank_wdi:SH.MED.PHYS.ZS", "world_bank_wdi:NE.TRD.GNFS.ZS", [1990, 2023], ["life_expectancy_health", "trade_liberalisation"], ["trade_policy"], ["medicine_access", "trade_openness"]),
    ("healthcare", "market_income_channel_health_outcomes", "Higher market-enabled income predicts better health outcomes over long windows.", "world_bank_wdi:SP.DYN.LE00.IN", "world_bank_wdi:NY.GDP.PCAP.KD", [1970, 2023], ["life_expectancy_health", "gdp_growth"], ["institutional_reform"], ["income_channel", "health_outcomes"]),
    ("healthcare", "medical_device_trade_openness_outcomes", "Medical-device import openness proxies predict faster diffusion of medical capacity.", "world_bank_wdi:SH.MED.BEDS.ZS", "world_bank_wdi:NE.TRD.GNFS.ZS", [1990, 2023], ["life_expectancy_health", "trade_liberalisation"], ["trade_policy"], ["medical_device_access", "trade_openness"]),
    ("healthcare", "market_institutions_health_spending_efficiency", "Stronger regulatory quality predicts more health output per unit of health spending.", "world_bank_wdi:SP.DYN.LE00.IN", "wgi:RQ.EST", [1996, 2023], ["life_expectancy_health", "fiscal_policy"], ["regulation", "welfare_architecture"], ["health_efficiency", "regulatory_quality"]),
    ("growth", "market_income_school_completion", "Market-led income growth predicts higher school completion over 20-year windows.", "world_bank_wdi:SE.SEC.CUAT.UP.ZS", "world_bank_wdi:NY.GDP.PCAP.KD", [1990, 2023], ["productivity", "gdp_growth"], ["institutional_reform"], ["income_growth", "school_completion"]),
    ("growth", "market_reform_female_education", "Market-led income growth predicts female education gains in low- and middle-income countries.", "world_bank_wdi:SE.SEC.CUAT.UP.FE.ZS", "world_bank_wdi:NY.GDP.PCAP.KD", [1990, 2023], ["productivity", "poverty_inequality"], ["institutional_reform"], ["female_education", "income_growth"]),
    ("housing", "housing_supply_freedom_affordability", "More permissive housing supply regulation proxies predict lower house-price pressure over long windows.", "bis:WS_SPP", "wgi:RQ.EST", [1996, 2024], ["housing"], ["housing_policy", "regulation"], ["housing_supply_freedom", "regulatory_quality"]),
    ("housing", "land_use_regulation_real_wage_drag", "Stricter land-use regulation proxies predict weaker real disposable wage and income gains via housing costs.", "world_bank_wdi:NY.GDP.PCAP.KD", "bis:WS_SPP", [1996, 2024], ["housing", "wage_stagnation"], ["housing_policy", "regulation"], ["land_use_regulation", "real_wage_drag"]),
    ("housing", "property_rights_mortgage_depth_home_access", "Stronger property rights and deeper credit markets predict broader long-run home access proxies.", "bis:WS_SPP", "wgi:RL.EST", [1996, 2024], ["housing", "institutional_quality"], ["institutional_reform", "housing_policy"], ["property_rights", "mortgage_depth"]),
    ("housing", "energy_market_competition_household_cost", "Stronger regulatory quality in energy markets predicts better household energy access and affordability proxies.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "welfare_state"], ["energy_policy", "regulation"], ["energy_competition", "electricity_access"]),
    ("labour", "labor_market_flexibility_employment_qol", "More flexible market-compatible institutions predict higher employment and quality-of-life opportunity.", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "welfare_state"], ["labour_market", "regulation"], ["labour_flexibility", "employment"]),
    ("labour", "employment_protection_youth_unemployment_long_run", "Stronger regulatory quality and labour-market openness predict lower youth unemployment over long windows.", "world_bank_wdi:SL.UEM.1524.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour"], ["labour_market", "regulation"], ["employment_protection", "youth_unemployment"]),
    ("labour", "payroll_tax_labor_force_participation", "Higher tax burden proxies predict lower labour-force participation over long windows.", "world_bank_wdi:SL.TLF.CACT.ZS", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", [1990, 2023], ["employment_labour", "taxation"], ["tax_policy", "labour_market"], ["payroll_tax", "labour_force_participation"]),
    ("labour", "female_lfp_market_opportunity", "Market opportunity and service-sector expansion predict higher female labour-force participation.", "world_bank_wdi:SL.TLF.CACT.FE.ZS", "world_bank_wdi:NV.SRV.TOTL.ZS", [1990, 2023], ["employment_labour", "poverty_inequality"], ["labour_market", "competition_policy"], ["female_lfp", "service_sector"]),
    ("regulatory", "financial_market_depth_productivity", "Deeper private financial markets predict stronger productivity and income growth by reallocating capital.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "world_bank_wdi:FS.AST.PRVT.GD.ZS", [1980, 2023], ["productivity", "capital_flows"], ["regulation"], ["financial_depth", "productivity"]),
    ("energy", "private_generation_entry_electrification", "Private and market-compatible generation entry proxies predict faster electrification.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "welfare_state"], ["energy_policy", "regulation"], ["private_generation", "electrification"]),
    ("institutional_quality", "economic_freedom_corruption_decline", "Market-compatible institutions predict higher control-of-corruption scores where rule of law constrains discretion.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality"], ["institutional_reform", "regulation"], ["economic_freedom", "corruption_decline"]),
]


def spec_for(case):
    topic, hid, claim, outcome_source, treatment_source, period, dims, families, tags = case
    spec = {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "methodology_note": "Promoted from the 200-item long-horizon market/QOL backlog as a local-data first-pass screen.",
        "evidence_type": "associational",
        "sample": {
            "countries": SAMPLE,
            "period": period,
            "temporal_structure": "panel",
            "exclusion_rules": ["drop country-years with missing primary outcome or treatment proxy"],
        },
        "scope": {
            "period": period,
            "countries": ["GLOBAL"],
            "outcome_dim": dims,
            "policy_family": families,
            "treatment_tags": tags,
        },
        "variables": {
            "outcome": [{"name": "qol_or_prosperity_outcome", "source": outcome_source, "transformation": "level_or_growth_proxy"}],
            "treatment": [{"name": "market_or_intervention_proxy", "source": treatment_source, "transformation": "level"}],
            "controls": [
                {"name": "log_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "rule_of_law", "source": "wgi:RL.EST", "transformation": "level"},
            ],
        },
        "estimator": {
            "template": "panel_fe",
            "fixed_effects": ["country", "year"],
            "clustering": "country",
            "notes": "Local-data first-pass TWFE screen; upgrade to exact outcome/treatment datasets before scoreboard promotion.",
        },
        "falsification": {
            "rule": "SUPPORTED if the treatment coefficient has the predicted sign at p<0.10. REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL.",
            "test": f"panel_fe_{hid}",
            "threshold": "p<0.10 with pre-registered sign",
        },
        "prior_confidence": 0.55,
        "disclosure": "These are proxy-first QOL screens. They are intended to identify promising evidence, not to settle causal claims without robustness checks.",
        "steelman": f"hypotheses/steelman/{hid}.md",
    }
    if hid == "tax_simplicity_disposable_income_growth":
        spec["falsification"]["threshold"] = {"p_value": "p<0.10", "expected_sign": "-"}
    elif hid == "economic_freedom_corruption_decline":
        spec["falsification"]["threshold"] = {"p_value": "p<0.10", "expected_sign": "+"}
    return spec


def main() -> int:
    created = 0
    for case in CASES:
        topic, hid = case[0], case[1]
        out_dir = ROOT / "hypotheses" / topic
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{hid}.yaml"
        if not path.exists():
            text = "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
            text += yaml.safe_dump(spec_for(case), sort_keys=False, width=100)
            path.write_text(text)
            created += 1
        steel = ROOT / "hypotheses" / "steelman" / f"{hid}.md"
        if not steel.exists():
            steel.write_text(
                f"# Steelman - {hid}\n\n"
                "The strongest objection is that this first-pass test uses broad local proxies. "
                "A policy-grade verdict needs exact treatment coding, robustness windows, and a check that income, state capacity, or demographic composition is not driving the association.\n"
            )
    print(f"created {created} QOL first-wave specs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
