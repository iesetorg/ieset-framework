#!/usr/bin/env python3
"""Promote the first-wave sectoral backlog IDs into candidate specs.

The generated specs are intentionally proxy-first: they use local WDI/WHO/OECD/
BIS/WGI variables plus explicit constructed treatment indicators. Exact sector
datasets can replace these variables later without losing the hypothesis IDs.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = [
    "USA", "GBR", "CAN", "AUS", "NZL", "DEU", "FRA", "ITA", "ESP", "NLD",
    "SWE", "NOR", "DNK", "FIN", "JPN", "KOR", "CHN", "IND", "BRA", "MEX",
    "CHL", "ARG", "TUR", "ZAF", "POL", "EST", "VNM", "THA", "MYS", "IDN",
]


CASES = [
    # Agriculture
    ("growth", "household_responsibility_system_china_agricultural_surge", "China's agricultural output growth accelerated after the household responsibility system replaced collective farming, relative to comparable middle-income reform peers.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for CHN from 1978 onward", [1970, 2023], ["productivity", "gdp_growth"], ["privatisation_nationalisation", "institutional_reform"], ["household_responsibility_system", "agricultural_property_rights"]),
    ("growth", "price_controls_food_output_decline_panel", "Countries maintaining long-lived food price controls or state procurement show slower agricultural value-added growth than market-priced peers.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for ARG from 2006 onward; ZWE from 2000 onward; ZMB from 1980 onward", [1970, 2023], ["productivity", "regulation_compliance_cost"], ["regulation"], ["food_price_controls", "state_procurement"]),
    ("growth", "smallholder_vs_plantation_yield_frontier", "Smallholder-dominant systems converge to higher long-run agricultural productivity than plantation-dominant systems after controlling for crop mix and land quality.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for VNM from 1988 onward; THA from 1980 onward; KOR from 1970 onward", [1970, 2023], ["productivity"], ["institutional_reform"], ["smallholder_farming", "land_tenure"]),
    ("growth", "gm_crop_adoption_yield_convergence", "Countries permitting GM crop cultivation without prolonged moratoria experienced faster agricultural yield convergence than ban or delay countries.", "world_bank_wdi:AG.PRD.CROP.XD", "constructed: 1 for USA from 1996 onward; ARG from 1996 onward; BRA from 2003 onward; CAN from 1996 onward", [1990, 2023], ["productivity", "regulation_compliance_cost"], ["regulation"], ["gm_crop_adoption", "biotech_regulation"]),
    ("growth", "land_reform_compensation_investment_recovery", "Market-compatible land reforms with compensation show stronger post-reform agricultural investment and productivity recovery than expropriatory reforms.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for CHL from 1974 onward; ZAF from 1994 onward; ZWE from 2000 onward", [1970, 2023], ["productivity", "institutional_quality"], ["institutional_reform", "privatisation_nationalisation"], ["compensated_land_reform", "expropriation"]),
    ("trade", "export_openness_agricultural_diversification", "Agricultural export liberalisation predicts faster diversification into higher-value crops than import-substitution agricultural policy.", "world_bank_wdi:TX.VAL.AGRI.ZS.UN", "constructed: 1 for CHL from 1975 onward; NZL from 1984 onward; VNM from 1988 onward", [1970, 2023], ["trade_liberalisation", "productivity"], ["trade_policy"], ["agricultural_export_openness"]),
    ("growth", "farm_size_regulation_inefficiency_panel", "Hard ceilings on farm size predict lower agricultural labour productivity after 20 years than market-determined scale.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for IND from 1972 onward; MEX from 1970 onward; ZAF from 1994 onward", [1970, 2023], ["productivity", "regulation_compliance_cost"], ["regulation"], ["farm_size_ceiling", "land_use_regulation"]),
    ("trade", "cotton_monopsony_state_board_vs_market", "Abolition of state cotton marketing boards predicts higher output and yield growth relative to state monopsony regimes.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for ZMB from 1994 onward; ZAF from 1996 onward; IND from 2002 onward", [1970, 2023], ["productivity", "competition_concentration"], ["privatisation_nationalisation", "competition_policy"], ["cotton_marketing_board", "state_monopsony"]),
    ("growth", "dairy_quota_abolition_output_response", "Removal of dairy production quotas predicts output expansion and price normalisation without persistent farm-income collapse.", "world_bank_wdi:NV.AGR.TOTL.ZS", "constructed: 1 for CAN from 1995 onward; NZL from 1984 onward; EU from 2015 onward", [1980, 2023], ["productivity", "competition_concentration"], ["regulation", "competition_policy"], ["dairy_quota_abolition"]),
    # Tech
    ("regulatory", "spectrum_auction_vs_administrative_allocation_telecom", "Countries moving from administrative spectrum allocation to market auctions show faster mobile and internet diffusion.", "world_bank_wdi:IT.NET.USER.ZS", "constructed: 1 for USA from 1994 onward; GBR from 2000 onward; DEU from 2000 onward; IND from 2010 onward", [1990, 2023], ["productivity", "competition_concentration"], ["competition_policy", "regulation"], ["spectrum_auction", "telecom_liberalisation"]),
    ("regulatory", "platform_competition_dissipates_monopoly_rent", "Technology markets with sustained multi-platform competition show faster quality-adjusted improvement than markets protected by interoperability barriers.", "world_bank_wdi:IT.NET.USER.ZS", "constructed: 1 for USA from 2000 onward; KOR from 2000 onward; EST from 2004 onward", [1995, 2023], ["competition_concentration", "productivity"], ["competition_policy", "regulation"], ["platform_competition", "interoperability"]),
    ("trade", "tech_transfer_restrictions_slow_catch_up", "Strict local-content or technology-transfer requirements on FDI slow high-tech productivity convergence over long windows.", "world_bank_wdi:TX.VAL.TECH.MF.ZS", "constructed: 1 for CHN from 2001 onward; IND from 1991 onward; BRA from 2003 onward", [1990, 2023], ["productivity", "trade_liberalisation"], ["trade_policy", "industrial_policy"], ["technology_transfer_requirements", "local_content"]),
    ("energy", "electric_vehicle_mandate_vs_market_adoption_path", "Consumer subsidies and charging-network markets predict more durable EV adoption than production quotas or manufacturer mandates after subsidy withdrawal.", "owid:electric-car-sales", "constructed: 1 for NOR from 2010 onward; CHN from 2015 onward; USA from 2010 onward", [2010, 2024], ["energy", "regulation_compliance_cost"], ["energy_policy", "industrial_policy"], ["electric_vehicle_mandate", "consumer_subsidy"]),
    # Healthcare
    ("healthcare", "market_healthcare_supply_mortality_amenable_panel", "Countries with more market-responsive hospital and physician supply show larger declines in amenable mortality over 20-year panels.", "world_bank_wdi:SH.DYN.MORT", "constructed: 1 for CHE from 1996 onward; NLD from 2006 onward; DEU from 1996 onward", [1996, 2023], ["life_expectancy_health"], ["welfare_architecture", "regulation"], ["private_healthcare_supply", "physician_entry"]),
    ("healthcare", "certificate_of_need_hospital_access_restrictions", "US-style Certificate-of-Need restrictions predict slower capacity growth and weaker health-access improvement than non-CON regimes.", "world_bank_wdi:SH.MED.BEDS.ZS", "constructed: 1 for USA from 1975 onward", [1975, 2023], ["life_expectancy_health", "regulation_compliance_cost"], ["regulation", "welfare_architecture"], ["certificate_of_need", "hospital_capacity"]),
    ("healthcare", "health_savings_account_preventive_spending", "Health-savings-account or catastrophic-plus-savings designs contain cost growth without worse age-adjusted mortality than comprehensive public-insurance peers.", "world_bank_wdi:SH.XPD.CHEX.GD.ZS", "constructed: 1 for SGP from 1984 onward; USA from 2003 onward", [1980, 2023], ["life_expectancy_health", "fiscal_policy"], ["welfare_architecture", "tax_policy"], ["health_savings_account", "catastrophic_insurance"]),
    ("healthcare", "physician_supply_cap_residency_constraint_mortality", "State-capped medical-school or residency places predict slower physician-supply growth and weaker mortality improvement in ageing populations.", "world_bank_wdi:SH.MED.PHYS.ZS", "constructed: 1 for USA from 1997 onward; CAN from 1993 onward; GBR from 1990 onward", [1990, 2023], ["life_expectancy_health", "employment_labour"], ["regulation", "welfare_architecture"], ["physician_supply_cap", "residency_constraint"]),
    ("healthcare", "dialysis_market_competition_outcome_quality", "Kidney-dialysis markets with competing providers and outcome-based reimbursement show lower mortality and hospitalisation than single-provider models.", "world_bank_wdi:SH.DYN.MORT", "constructed: 1 for USA from 1983 onward; DEU from 1990 onward; JPN from 1990 onward", [1980, 2023], ["life_expectancy_health", "competition_concentration"], ["competition_policy", "welfare_architecture"], ["dialysis_competition", "outcome_based_reimbursement"]),
    ("healthcare", "imaging_equipment_market_entry_wait_times", "Countries liberalising medical-imaging equipment licensing and private-clinic entry show larger reductions in diagnostic wait times.", "world_bank_wdi:SH.MED.BEDS.ZS", "constructed: 1 for JPN from 1990 onward; KOR from 1995 onward; DEU from 1990 onward", [1990, 2023], ["life_expectancy_health", "regulation_compliance_cost"], ["regulation", "competition_policy"], ["imaging_equipment_entry", "clinic_liberalisation"]),
    ("healthcare", "generic_substitution_mandate_savings_no_harm", "Mandatory pharmacy-level generic substitution predicts pharmaceutical-spending reductions without worse mortality outcomes.", "world_bank_wdi:SH.XPD.CHEX.PC.CD", "constructed: 1 for DEU from 2002 onward; SWE from 2002 onward; USA from 1984 onward", [1980, 2023], ["life_expectancy_health", "fiscal_policy"], ["regulation", "welfare_architecture"], ["generic_substitution", "pharma_spending"]),
    ("healthcare", "ophthalmology_laser_surgery_market_price_trajectory", "Private competition in cataract and refractive surgery markets predicts long-run real-price decline and technology adoption.", "world_bank_wdi:SH.XPD.CHEX.PC.CD", "constructed: 1 for USA from 1995 onward; GBR from 2000 onward; KOR from 2000 onward", [1990, 2023], ["life_expectancy_health", "competition_concentration"], ["competition_policy", "welfare_architecture"], ["ophthalmology_competition", "elective_surgery_market"]),
    # Housing
    ("housing", "rent_control_housing_supply_destruction_panel", "Stringent rent control predicts slower rental-stock growth and higher uncontrolled market rents over long city or country panels.", "bis:WS_SPP", "constructed: 1 for USA from 1970 onward; DEU from 2015 onward; SWE from 1970 onward", [1970, 2024], ["housing", "regulation_compliance_cost"], ["housing_policy", "regulation"], ["rent_control", "rental_supply"]),
    ("housing", "zoning_deregulation_housing_affordability", "Upzoning and deregulation of single-family-only zoning predict faster permit growth and lower real rent growth than restrictive zoning.", "bis:WS_SPP", "constructed: 1 for NZL from 2016 onward; USA from 2019 onward; JPN from 2002 onward", [1990, 2024], ["housing", "regulation_compliance_cost"], ["housing_policy", "regulation"], ["zoning_deregulation", "upzoning"]),
    ("housing", "housing_voucher_mobility_vs_project_concentration", "Tenant-based vouchers predict better long-run neighbourhood and earnings outcomes than project-based public housing in high-poverty tracts.", "world_bank_wdi:NY.GDP.PCAP.KD", "constructed: 1 for USA from 1994 onward; GBR from 1988 onward", [1980, 2023], ["housing", "poverty_inequality"], ["housing_policy", "welfare_architecture"], ["housing_vouchers", "public_housing"]),
    ("housing", "land_value_tax_vacant_lot_utilisation", "Land-value or split-rate property taxation predicts lower vacancy and faster redevelopment than pure improvement taxation.", "world_bank_wdi:NY.GDP.PCAP.KD", "constructed: 1 for EST from 1993 onward; AUS from 1980 onward; USA from 1979 onward", [1970, 2023], ["housing", "taxation"], ["tax_policy", "housing_policy"], ["land_value_tax", "split_rate_property_tax"]),
    ("housing", "growth_boundary_urban_house_price_inflation", "Urban growth boundaries or greenbelts predict steeper house-price-to-income ratios and lower construction-employment growth.", "bis:WS_SPP", "constructed: 1 for GBR from 1955 onward; NZL from 1991 onward; USA from 1979 onward", [1970, 2024], ["housing", "regulation_compliance_cost"], ["housing_policy", "regulation"], ["urban_growth_boundary", "greenbelt"]),
    ("housing", "building_height_limit_downtown_productivity", "Strict building-height restrictions near transit nodes predict lower agglomeration productivity and higher office or housing costs.", "world_bank_wdi:NY.GDP.PCAP.KD", "constructed: 1 for USA from 1910 onward; FRA from 1977 onward; IND from 1990 onward", [1970, 2023], ["housing", "productivity"], ["housing_policy", "regulation"], ["height_limits", "agglomeration"]),
    ("housing", "social_housing_privatisation_tenant_wealth", "Right-to-buy and social-housing privatisation transfers predict higher household wealth accumulation than continued state ownership.", "world_bank_wdi:NY.GDP.PCAP.KD", "constructed: 1 for GBR from 1980 onward; NZL from 1991 onward; SWE from 1991 onward", [1970, 2023], ["housing", "poverty_inequality"], ["housing_policy", "privatisation_nationalisation"], ["right_to_buy", "social_housing_privatisation"]),
    ("housing", "construction_permit_time_gdp_cost", "Longer construction-permit approval times predict higher construction costs and lower housing-output elasticity.", "world_bank_wdi:IC.CNST.PRMT", "constructed: 1 for IND from 2005 onward; BRA from 2005 onward; ZAF from 2005 onward", [2005, 2023], ["housing", "regulation_compliance_cost"], ["housing_policy", "regulation"], ["construction_permit_time", "building_permits"]),
    ("housing", "mortgage_interest_deduction_homeownership_rate", "Large mortgage-interest deductions do not raise long-run homeownership rates but do raise house-price-to-income ratios.", "bis:WS_SPP", "constructed: 1 for USA from 1986 onward; NLD from 1990 onward; SWE from 1990 onward", [1980, 2024], ["housing", "taxation"], ["tax_policy", "housing_policy"], ["mortgage_interest_deduction"]),
    ("housing", "parking_minimum_abolition_housing_cost", "Abolishing parking minimums near transit predicts lower per-unit construction costs and faster multifamily permitting.", "world_bank_wdi:IC.CNST.PRMT", "constructed: 1 for NZL from 2020 onward; USA from 2017 onward; GBR from 2001 onward", [2000, 2023], ["housing", "regulation_compliance_cost"], ["housing_policy", "regulation"], ["parking_minimum_abolition"]),
    # Cross-sector
    ("regulatory", "price_signal_sectoral_reallocation_speed", "Stronger market price signals and lower sector-entry barriers predict faster labour reallocation during terms-of-trade shocks.", "world_bank_wdi:SL.SRV.EMPL.ZS", "wgi:RQ.EST", [1996, 2023], ["employment_labour", "productivity"], ["regulation", "competition_policy"], ["price_signals", "sectoral_reallocation"]),
    ("institutional_quality", "regulatory_predictability_cross_sector_investment", "Stable rules-based regulation predicts higher cross-sector private investment and faster technology adoption than discretionary intervention.", "world_bank_wdi:NE.GDI.FTOT.ZS", "wgi:RQ.EST", [1996, 2023], ["institutional_quality", "capital_flows"], ["institutional_reform", "regulation"], ["regulatory_predictability", "private_investment"]),
    ("regulatory", "market_entry_uniform_code_productivity", "Unified national building, sanitary, and product standards predict faster cross-regional firm entry and higher productivity than fragmented subnational regulation.", "world_bank_wdi:NY.GDP.PCAP.KD.ZG", "wgi:RQ.EST", [1996, 2023], ["productivity", "competition_concentration"], ["regulation", "competition_policy"], ["uniform_codes", "market_entry"]),
    ("fiscal", "sector_neutral_tax_vs_exemption_cumulation", "Low-rate broad-base tax systems predict stronger long-run investment and employment than high-rate systems with sector exemptions.", "world_bank_wdi:NE.GDI.FTOT.ZS", "world_bank_wdi:GC.TAX.TOTL.GD.ZS", [1990, 2023], ["taxation", "capital_flows", "employment_labour"], ["tax_policy", "fiscal_policy"], ["broad_base_taxation", "sector_exemptions"]),
]


def spec_for(case):
    topic, hid, claim, outcome_source, treatment_source, period, dims, families, tags = case
    countries = SAMPLE
    return {
        "hypothesis_id": hid,
        "version": 1,
        "status": "candidate",
        "topic": topic,
        "claim": claim,
        "methodology_note": "Promoted from the sectoral first-wave backlog on 2026-05-02 using locally cached proxy variables; exact sector datasets can replace proxies in later revisions.",
        "evidence_type": "associational",
        "sample": {
            "countries": countries,
            "period": period,
            "temporal_structure": "panel",
            "exclusion_rules": ["drop country-years with missing primary outcome or treatment proxy"],
        },
        "variables": {
            "outcome": [{"name": "primary_sectoral_outcome", "source": outcome_source, "transformation": "level_or_growth_proxy"}],
            "treatment": [{"name": "policy_or_institution_proxy", "source": treatment_source, "transformation": "indicator_or_level"}],
            "controls": [
                {"name": "log_gdp_pc", "source": "world_bank_wdi:NY.GDP.PCAP.KD", "transformation": "log"},
                {"name": "rule_of_law", "source": "wgi:RL.EST", "transformation": "level"},
            ],
        },
        "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country", "notes": "Proxy-first TWFE screen; upgrade to bespoke replication when exact sector datasets are fetched."},
        "falsification": {"rule": "SUPPORTED if the treatment coefficient has the predicted sign at p<0.10. REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL.", "test": f"panel_fe_{hid}", "threshold": "p<0.10 with pre-registered sign"},
        "prior_confidence": 0.55,
        "disclosure": "Proxy-first promotion risk: the local variable may capture broad institutional or sector conditions rather than the exact legal treatment. Treat first-pass verdicts as triage until exact datasets are fetched.",
        "steelman": f"hypotheses/steelman/{hid}.md",
        "scope": {"period": period, "countries": ["GLOBAL"], "outcome_dim": dims, "policy_family": families, "treatment_tags": tags},
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
                f"# Steelman — {hid}\n\n"
                "The strongest counter is that this first-wave spec uses broad local proxies rather than the exact sectoral legal or administrative dataset. "
                "A clean verdict requires replacing the proxy treatment with direct reform coding, checking pre-trends, and separating transition costs from long-run equilibrium effects.\n"
            )
    print(f"created {created} sectoral specs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
