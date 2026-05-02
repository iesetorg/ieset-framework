#!/usr/bin/env python3
"""Promote a third QOL/free-market long-horizon wave.

This wave is designed to push the free-market/QOL research agenda past 100
locally run hypotheses. It selects unpromoted backlog items that can be screened
with already-local WDI/WGI/BIS-style proxies.
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
    ("growth", "education_choice_learning_outcomes", "Higher market-compatible regulatory quality predicts stronger secondary-school enrollment outcomes over long windows.", "world_bank_wdi:SE.SEC.ENRR", "wgi:RQ.EST", [1996, 2023], ["productivity", "welfare_state"], ["regulation", "competition_policy"], ["education_choice", "regulatory_quality"], "+"),
    ("growth", "private_school_entry_education_quality", "Higher regulatory quality and lower entry-barrier proxies predict stronger education participation outcomes.", "world_bank_wdi:SE.SEC.ENRR", "wgi:RQ.EST", [1996, 2023], ["productivity", "regulation_compliance_cost"], ["regulation", "competition_policy"], ["private_school_entry", "education_quality"], "+"),
    ("growth", "tertiary_autonomy_research_output", "Higher institutional and regulatory quality predicts stronger tertiary education participation and research-capacity proxies.", "world_bank_wdi:SE.TER.ENRR", "wgi:GE.EST", [1996, 2023], ["productivity", "institutional_quality"], ["institutional_reform", "regulation"], ["tertiary_autonomy", "research_capacity"], "+"),
    ("growth", "education_spending_vs_school_autonomy", "School-autonomy and governance-quality proxies predict education gains beyond income levels alone.", "world_bank_wdi:SE.SEC.ENRR", "wgi:GE.EST", [1996, 2023], ["productivity", "welfare_state"], ["institutional_reform", "regulation"], ["school_autonomy", "education_quality"], "+"),
    ("growth", "human_capital_market_reform_lag", "Market-compatible regulatory quality predicts stronger human-capital accumulation with long lags.", "world_bank_wdi:SE.TER.ENRR", "wgi:RQ.EST", [1996, 2023], ["productivity", "institutional_quality"], ["institutional_reform", "regulation"], ["human_capital", "market_reform_lag"], "+"),
    ("growth", "education_qol_market_broad_sample", "Market-compatible institutional quality predicts education-related quality-of-life gains across broad samples.", "world_bank_wdi:SE.ADT.LITR.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "welfare_state"], ["institutional_reform", "regulation"], ["education_qol", "market_institutions"], "+"),
    ("housing", "market_housing_supply_migration_opportunity", "Higher market-compatible regulatory quality predicts stronger migration opportunity and population-mobility proxies.", "world_bank_wdi:SM.POP.NETM", "wgi:RQ.EST", [1996, 2023], ["housing", "demographics_migration"], ["housing_policy", "regulation"], ["housing_supply", "migration_opportunity"], "+"),
    ("housing", "construction_competition_housing_cost", "Higher market-compatible regulatory quality predicts lower broad house-price pressure through construction competition.", "bis:WS_SPP", "wgi:RQ.EST", [1996, 2024], ["housing"], ["housing_policy", "competition_policy"], ["construction_competition", "housing_cost"], "-"),
    ("housing", "urban_services_private_entry_quality", "Higher regulatory quality predicts better urban-service availability proxies over long windows.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["housing", "energy"], ["regulation", "energy_policy"], ["urban_services", "private_entry"], "+"),
    ("housing", "transport_market_entry_commute_qol", "Higher regulatory quality predicts better transport-access proxies and commute-related quality of life.", "world_bank_wdi:IS.RRS.PASG.KM", "wgi:RQ.EST", [1996, 2023], ["housing", "welfare_state"], ["regulation", "competition_policy"], ["transport_entry", "commute_qol"], "+"),
    ("housing", "housing_tax_distortion_mobility", "Higher broad tax-burden proxies predict weaker population-mobility and housing-opportunity matching.", "world_bank_wdi:SM.POP.NETM", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", [1996, 2023], ["housing", "taxation"], ["tax_policy", "housing_policy"], ["transaction_taxes", "mobility"], "-"),
    ("housing", "land_title_formalization_investment", "Stronger rule-of-law and property-rights proxies predict higher investment rates and neighborhood-upgrading capacity.", "world_bank_wdi:NE.GDI.TOTL.ZS", "wgi:RL.EST", [1996, 2023], ["housing", "capital_flows"], ["institutional_reform", "housing_policy"], ["land_title", "property_rights"], "+"),
    ("labour", "occupational_licensing_income_mobility", "Higher regulatory quality predicts stronger income mobility proxies than discretionary licensing-heavy systems.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "gdp_growth"], ["labour_market", "regulation"], ["occupational_licensing", "income_mobility"], "+"),
    ("labour", "labor_reform_real_wage_growth", "Higher market-compatible regulatory quality predicts stronger long-run real wage and income proxies.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RQ.EST", [1996, 2023], ["wage_stagnation", "employment_labour"], ["labour_market", "regulation"], ["labor_reform", "real_wage_growth"], "+"),
    ("labour", "migration_labor_market_openness_qol", "Higher market-compatible regulatory quality predicts stronger migration-opportunity and labor-market openness proxies.", "world_bank_wdi:SM.POP.NETM", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "demographics_migration"], ["labour_market", "regulation"], ["migration_openness", "labor_market_openness"], "+"),
    ("labour", "informality_entry_barriers_labor_qol", "Higher regulatory quality predicts stronger employment-rate proxies where entry barriers and informality are lower.", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "regulation_compliance_cost"], ["labour_market", "regulation"], ["informality", "entry_barriers"], "+"),
    ("labour", "market_reform_job_quality_panel", "Market-compatible regulatory quality predicts stronger job-quality proxies measured by employment and income levels.", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "wage_stagnation"], ["labour_market", "regulation"], ["market_reform", "job_quality"], "+"),
    ("labour", "portable_benefits_market_flexibility", "Market-compatible regulatory quality predicts higher labor-force participation where benefits can remain portable.", "world_bank_wdi:SL.TLF.CACT.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "welfare_state"], ["labour_market", "welfare_architecture"], ["portable_benefits", "market_flexibility"], "+"),
    ("labour", "labor_market_market_qol_broad_scope", "Market-friendly labor institutions predict stronger broad opportunity measures across long samples.", "world_bank_wdi:SL.EMP.TOTL.SP.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "welfare_state"], ["labour_market", "regulation"], ["labor_market_broad_scope", "market_institutions"], "+"),
    ("regulatory", "market_competition_patent_quality", "Higher regulatory quality and competition proxies predict stronger high-technology export and innovation-quality proxies.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "competition_concentration"], ["competition_policy", "regulation"], ["competition", "patent_quality"], "+"),
    ("institutional_quality", "ip_protection_innovation_diffusion", "Stronger rule-of-law and IP-protection proxies predict stronger high-technology diffusion and innovation outputs.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RL.EST", [1996, 2023], ["productivity", "institutional_quality"], ["institutional_reform", "regulation"], ["ip_protection", "innovation_diffusion"], "+"),
    ("regulatory", "state_rd_vs_private_rd_productivity", "Deeper private financial-market proxies predict stronger productivity growth than state-directed allocation alone.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "world_bank_wdi:FS.AST.PRVT.GD.ZS", [1996, 2023], ["productivity", "capital_flows"], ["regulation", "industrial_policy"], ["private_rd", "capital_allocation"], "+"),
    ("regulatory", "venture_capital_market_depth_innovation", "Deeper private financial-market proxies predict stronger high-technology and innovation diffusion outcomes.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "world_bank_wdi:FS.AST.PRVT.GD.ZS", [1996, 2023], ["productivity", "capital_flows"], ["regulation", "competition_policy"], ["venture_capital", "market_depth"], "+"),
    ("trade", "open_standards_market_diffusion", "Greater trade openness predicts stronger high-technology diffusion under open competitive standards.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "world_bank_wdi:NE.TRD.GNFS.ZS", [1996, 2023], ["productivity", "trade_liberalisation"], ["trade_policy", "competition_policy"], ["open_standards", "technology_diffusion"], "+"),
    ("regulatory", "innovation_cluster_market_entry", "Higher regulatory quality predicts stronger innovation-cluster proxies through firm entry and labor mobility.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "regulation_compliance_cost"], ["regulation", "competition_policy"], ["innovation_cluster", "market_entry"], "+"),
    ("growth", "innovation_qol_market_spillovers", "High-technology diffusion predicts stronger income and quality-of-life spillovers over long windows.", "world_bank_wdi:NY.GDP.PCAP.KD", "world_bank_wdi:TX.VAL.TECH.MF.ZS", [1996, 2023], ["productivity", "gdp_growth"], ["competition_policy", "trade_policy"], ["innovation_spillovers", "quality_of_life"], "+"),
    ("regulatory", "market_innovation_broad_scope", "Market-compatible regulatory quality predicts stronger broad innovation outcomes than direct planning intensity.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "industrial_capability"], ["regulation", "competition_policy"], ["market_innovation", "broad_scope"], "+"),
    ("energy", "energy_market_competition_reliability", "Higher market-compatible regulatory quality predicts stronger electricity access and reliability proxies.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "welfare_state"], ["energy_policy", "regulation"], ["energy_competition", "reliability"], "+"),
    ("institutional_quality", "rule_bound_regulation_business_trust", "Rule-bound regulatory quality predicts higher control-of-corruption and business-trust governance proxies.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "regulation_compliance_cost"], ["regulation", "institutional_reform"], ["rule_bound_regulation", "business_trust"], "+"),
    ("institutional_quality", "regulatory_transparency_investment", "Regulatory transparency and quality predict higher long-run investment shares.", "world_bank_wdi:NE.GDI.TOTL.ZS", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "capital_flows"], ["regulation", "institutional_reform"], ["regulatory_transparency", "investment"], "+"),
]


def spec_for(case):
    topic, hid, claim, outcome_source, treatment_source, period, dims, families, tags, expected_sign = case
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "methodology_note": "Promoted from the third long-horizon market/QOL candidate wave as a local-data first-pass screen.",
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
            "notes": "Local-data first-pass TWFE screen; upgrade to exact treatment/outcome datasets before scoreboard promotion.",
        },
        "falsification": {
            "rule": "SUPPORTED if the treatment coefficient has the pre-registered sign at p<0.10. REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL.",
            "test": f"panel_fe_{hid}",
            "threshold": {"p_value": "p<0.10", "expected_sign": expected_sign},
        },
        "prior_confidence": 0.55,
        "disclosure": "These are proxy-first QOL screens. They are intended to identify promising evidence, not to settle causal claims without robustness checks.",
        "steelman": f"hypotheses/steelman/{hid}.md",
    }


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
                "The strongest objection is that this third-wave screen uses broad local proxies. "
                "A policy-grade verdict needs exact treatment coding, robustness windows, and a check "
                "that income, state capacity, demographics, or resource composition is not driving the association.\n"
            )
    print(f"created {created} QOL third-wave specs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
