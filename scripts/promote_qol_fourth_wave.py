#!/usr/bin/env python3
"""Promote a fourth QOL/free-market long-horizon wave.

This wave emphasizes the remaining innovation, infrastructure, energy, and
governance backlog items with local WDI/WGI/BIS-style proxies.
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
    ("regulatory", "incumbent_subsidy_innovation_drag", "Higher broad state-allocation burden proxies predict weaker high-technology innovation diffusion.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["productivity", "industrial_capability"], ["industrial_policy", "regulation"], ["incumbent_subsidy", "innovation_drag"], "-"),
    ("regulatory", "digital_regulation_startup_creation", "Higher market-compatible regulatory quality predicts stronger digital and high-technology startup proxies.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "regulation_compliance_cost"], ["regulation", "competition_policy"], ["digital_regulation", "startup_creation"], "+"),
    ("regulatory", "competition_ai_adoption_productivity", "Higher market-compatible regulatory quality predicts stronger productivity growth through faster technology adoption.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "wgi:RQ.EST", [1996, 2023], ["productivity", "gdp_growth"], ["competition_policy", "regulation"], ["competition", "technology_adoption"], "+"),
    ("regulatory", "state_champion_tech_failure_rate", "Higher state-allocation burden proxies predict weaker high-technology diffusion than competitive financing.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["productivity", "industrial_capability"], ["industrial_policy", "fiscal_policy"], ["state_champions", "technology_failure"], "-"),
    ("regulatory", "public_procurement_innovation_conditions", "Higher regulatory quality predicts stronger investment and innovation diffusion where procurement is more rule-bound.", "world_bank_wdi:NE.GDI.TOTL.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "capital_flows"], ["regulation", "competition_policy"], ["public_procurement", "innovation_conditions"], "+"),
    ("regulatory", "university_spinout_market_rules", "Higher market-compatible regulatory quality predicts stronger high-technology output from university spinout ecosystems.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "institutional_quality"], ["regulation", "competition_policy"], ["university_spinout", "market_rules"], "+"),
    ("regulatory", "bank_state_ownership_credit_misallocation", "Deeper private-credit market proxies predict stronger productivity growth than state-owned banking allocation.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "world_bank_wdi:FS.AST.PRVT.GD.ZS", [1996, 2023], ["productivity", "capital_flows"], ["regulation", "privatisation_nationalisation"], ["private_credit", "credit_misallocation"], "+"),
    ("regulatory", "regulatory_sandbox_entry_innovation", "Higher regulatory quality predicts stronger high-technology diffusion consistent with entry-permitting regulatory sandboxes.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RQ.EST", [1996, 2023], ["productivity", "regulation_compliance_cost"], ["regulation", "competition_policy"], ["regulatory_sandbox", "entry_innovation"], "+"),
    ("regulatory", "patent_thicket_intervention_drag", "Higher rule-of-law and regulatory-quality proxies predict stronger innovation diffusion than interventionist IP bottlenecks.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "wgi:RL.EST", [1996, 2023], ["productivity", "institutional_quality"], ["regulation", "institutional_reform"], ["patent_thicket", "innovation_drag"], "+"),
    ("energy", "water_utility_private_participation_quality", "Higher regulatory quality predicts stronger network-utility access proxies where private or corporatized participation is credible.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "welfare_state"], ["energy_policy", "regulation"], ["utility_participation", "access_quality"], "+"),
    ("energy", "state_monopoly_infrastructure_cost_overrun", "Higher state-allocation burden proxies predict weaker infrastructure access outcomes than competitive procurement.", "world_bank_wdi:EG.ELC.ACCS.ZS", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["energy", "fiscal_policy"], ["fiscal_policy", "industrial_policy"], ["state_monopoly", "infrastructure_cost"], "-"),
    ("energy", "road_freight_liberalization_logistics_quality", "Higher regulatory quality predicts stronger transport and logistics access proxies over long windows.", "world_bank_wdi:IS.RRS.PASG.KM", "wgi:RQ.EST", [1996, 2023], ["energy", "trade_liberalisation"], ["regulation", "competition_policy"], ["road_freight_liberalization", "logistics_quality"], "+"),
    ("trade", "port_competition_trade_cost", "Higher regulatory quality predicts higher trade openness through lower port and trade-cost frictions.", "world_bank_wdi:NE.TRD.GNFS.ZS", "wgi:RQ.EST", [1996, 2023], ["trade_liberalisation", "productivity"], ["trade_policy", "competition_policy"], ["port_competition", "trade_cost"], "+"),
    ("energy", "energy_qol_market_broad_scope", "Market-compatible regulatory quality predicts stronger broad energy-access quality-of-life outcomes.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "welfare_state"], ["energy_policy", "regulation"], ["energy_qol", "market_broad_scope"], "+"),
    ("energy", "infrastructure_user_pricing_quality", "Higher regulatory quality predicts stronger infrastructure-maintenance and access proxies than universal underpricing.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:RQ.EST", [1996, 2023], ["energy", "fiscal_policy"], ["energy_policy", "regulation"], ["user_pricing", "infrastructure_quality"], "+"),
    ("energy", "state_capacity_market_infrastructure_complement", "Infrastructure quality improves most where state capacity enables market-compatible regulation.", "world_bank_wdi:EG.ELC.ACCS.ZS", "wgi:GE.EST", [1996, 2023], ["energy", "institutional_quality"], ["energy_policy", "institutional_reform"], ["state_capacity", "market_infrastructure"], "+"),
    ("institutional_quality", "licensing_discretion_bribery", "Higher regulatory quality predicts higher control-of-corruption scores, consistent with lower licensing discretion and bribery.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "regulation_compliance_cost"], ["regulation", "institutional_reform"], ["licensing_discretion", "bribery"], "+"),
    ("institutional_quality", "market_reform_civil_liberties_interaction", "Higher market-compatible regulatory quality predicts stronger voice-and-accountability proxies in democracies and open institutions.", "wgi:GOV_WGI_VA.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "welfare_state"], ["regulation", "institutional_reform"], ["market_reform", "civil_liberties"], "+"),
    ("institutional_quality", "state_ownership_media_freedom", "Higher state-allocation burden proxies predict weaker voice-and-accountability and information-quality proxies.", "wgi:GOV_WGI_VA.EST", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["institutional_quality", "fiscal_policy"], ["privatisation_nationalisation", "fiscal_policy"], ["state_ownership", "media_freedom"], "-"),
    ("fiscal", "tax_complexity_trust_government", "Higher broad tax-burden proxies predict lower control-of-corruption and trust-related governance outcomes.", "wgi:CC.EST", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", [1996, 2023], ["institutional_quality", "taxation"], ["tax_policy", "institutional_reform"], ["tax_complexity", "trust_government"], "-"),
    ("institutional_quality", "property_rights_social_trust", "Stronger rule-of-law and property-rights proxies predict higher control-of-corruption and social-trust governance outcomes.", "wgi:CC.EST", "wgi:RL.EST", [1996, 2023], ["institutional_quality"], ["institutional_reform"], ["property_rights", "social_trust"], "+"),
    ("institutional_quality", "market_freedom_democratic_resilience", "Higher regulatory quality predicts stronger political-stability and democratic-resilience proxies.", "wgi:GOV_WGI_PV.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "welfare_state"], ["institutional_reform", "regulation"], ["market_freedom", "democratic_resilience"], "+"),
    ("institutional_quality", "crony_capitalism_not_market_freedom", "Higher regulatory quality predicts stronger control-of-corruption scores than discretionary crony-capitalist allocation.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "regulation_compliance_cost"], ["regulation", "institutional_reform"], ["crony_capitalism", "market_freedom"], "+"),
    ("institutional_quality", "procurement_competition_corruption", "Higher regulatory quality predicts higher control-of-corruption scores through more competitive procurement conditions.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "regulation_compliance_cost"], ["competition_policy", "regulation"], ["procurement_competition", "corruption"], "+"),
    ("fiscal", "campaign_favoritism_subsidy_allocation", "Higher state-allocation burden proxies predict weaker productivity growth through favoritism and subsidy allocation.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["gdp_growth", "fiscal_policy"], ["fiscal_policy", "industrial_policy"], ["campaign_favoritism", "subsidy_allocation"], "-"),
    ("institutional_quality", "judicial_independence_market_qol", "Stronger rule-of-law proxies strengthen quality-of-life and income outcomes under market institutions.", "world_bank_wdi:NY.GDP.PCAP.KD", "wgi:RL.EST", [1996, 2023], ["institutional_quality", "gdp_growth"], ["institutional_reform", "regulation"], ["judicial_independence", "market_qol"], "+"),
    ("institutional_quality", "federalism_market_experimentation", "Higher regulatory quality predicts stronger long-run growth consistent with decentralized market-policy experimentation.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "gdp_growth"], ["institutional_reform", "regulation"], ["federalism", "market_experimentation"], "+"),
    ("institutional_quality", "state_planning_information_quality", "Higher state-allocation burden proxies predict weaker voice-and-accountability information-quality outcomes.", "wgi:GOV_WGI_VA.EST", "world_bank_wdi:NE.CON.GOVT.ZS", [1996, 2023], ["institutional_quality", "fiscal_policy"], ["fiscal_policy", "industrial_policy"], ["state_planning", "information_quality"], "-"),
    ("institutional_quality", "economic_freedom_personal_freedom", "Higher market-compatible regulatory quality predicts stronger personal-freedom and voice-and-accountability proxies.", "wgi:GOV_WGI_VA.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "welfare_state"], ["institutional_reform", "regulation"], ["economic_freedom", "personal_freedom"], "+"),
    ("institutional_quality", "market_governance_qol_broad_scope", "Market-compatible institutions predict governance quality and quality-of-life outcomes jointly across broad samples.", "wgi:CC.EST", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "welfare_state"], ["institutional_reform", "regulation"], ["market_governance", "qol_broad_scope"], "+"),
]


def spec_for(case):
    topic, hid, claim, outcome_source, treatment_source, period, dims, families, tags, expected_sign = case
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "methodology_note": "Promoted from the fourth long-horizon market/QOL candidate wave as a local-data first-pass screen.",
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
                "The strongest objection is that this fourth-wave screen uses broad local proxies. "
                "A policy-grade verdict needs exact treatment coding, robustness windows, and a check "
                "that income, state capacity, demographics, or resource composition is not driving the association.\n"
            )
    print(f"created {created} QOL fourth-wave specs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
