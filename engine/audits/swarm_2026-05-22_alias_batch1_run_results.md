# Swarm 2026-05-22 NEEDS_ALIAS Batch 1 Run Results

This audit records the first-pass generic `panel_fe` execution of the 30 promoted alias-repair candidates.

These are triage verdicts only: no scoreboard mappings or claim links were added in this pass.

## Summary

- hypotheses attempted: 30
- diagnostics written: 30
- supported: 3
- refuted: 9
- partial: 18
- inconclusive_data_pending: 0
- alias repair: OECD SOCX programme filters now cover family benefits, childcare spending, and housing assistance proxies
- repair note: `ml_entry_barriers_informality_small_firm_productivity` uses Fraser regulation after OECD PMR entry barriers had no within-country FE variation

## Topic By Verdict

| topic | supported | refuted | partial | inconclusive | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| energy | 1 | 0 | 2 | 0 | 3 |
| fiscal | 1 | 2 | 5 | 0 | 8 |
| growth | 0 | 2 | 0 | 0 | 2 |
| healthcare | 0 | 0 | 1 | 0 | 1 |
| institutional_quality | 0 | 0 | 2 | 0 | 2 |
| labour | 0 | 4 | 5 | 0 | 9 |
| monetary | 0 | 0 | 1 | 0 | 1 |
| trade | 1 | 1 | 2 | 0 | 4 |

## Verdict Inventory

| hypothesis | topic | verdict | reason |
| --- | --- | --- | --- |
| `renewable_share_electricity_price_transition_cost_panel` | energy | SUPPORTED | coef=-0.001262 (sign matches claim -), p=0.0133 |
| `capacity_public_investment_execution_private_capital_complement` | fiscal | SUPPORTED | coef=+0.09608 (sign matches claim +), p=0.000708 |
| `industrial_policy_hightech_exports_patents_panel` | trade | SUPPORTED | coef=+3.443 (sign matches claim +), p=0.00454 |
| `automatic_stabilizers_recession_depth_recovery_panel` | fiscal | REFUTED | coef=+0.3715 (sign opposite claim -), p=0.00042 |
| `capacity_fiscal_expansion_slack_inflation_tradeoff` | fiscal | REFUTED | coef=-0.1062 (sign opposite claim +), p=0.0299 |
| `capacity_broadband_competition_productivity_diffusion` | growth | REFUTED | coef=-0.04359 (sign opposite claim +), p=7.92e-06 |
| `ml_capital_market_depth_reallocation_productivity` | growth | REFUTED | coef=-0.001099 (sign opposite claim +), p=0.00632 |
| `capacity_activation_spending_unemployment_duration` | labour | REFUTED | coef=+0.7581 (sign opposite claim -), p=0.0882 |
| `ml_tax_wedge_labor_participation_formality_panel` | labour | REFUTED | coef=+0.006566 (sign opposite claim -), p=0.00865 |
| `oecd_almp_spending_unemployment_recovery_panel` | labour | REFUTED | coef=+0.7581 (sign opposite claim -), p=0.0882 |
| `unemployment_benefit_generosity_stabilizer_vs_duration_panel` | labour | REFUTED | coef=+2.468 (sign opposite claim -), p=2.57e-08 |
| `ml_customs_simplification_trade_cost_growth` | trade | REFUTED | coef=+0.009358 (sign opposite claim -), p=0.0201 |
| `ml_network_unbundling_price_quality_telecom_energy` | energy | PARTIAL | coef=+0.9358, p=0.893 (above α=0.1); direction inconclusive |
| `public_investment_green_capacity_crowding_in_panel` | energy | PARTIAL | coef=-0.08316, p=0.266 (above α=0.1); direction inconclusive |
| `capacity_government_consumption_vs_investment_composition` | fiscal | PARTIAL | coef=+0.06252, p=0.278 (above α=0.1); direction inconclusive |
| `education_spending_low_income_attainment_mobility_panel` | fiscal | PARTIAL | coef=+1.338, p=0.17 (above α=0.1); direction inconclusive |
| `ml_corporate_tax_neutrality_capital_deepening_panel` | fiscal | PARTIAL | coef=-0.02514, p=0.702 (above α=0.1); direction inconclusive |
| `public_pension_generosity_elderly_poverty_fiscal_tradeoff` | fiscal | PARTIAL | coef=+0.01461, p=0.917 (above α=0.1); direction inconclusive |
| `social_spending_market_poverty_reduction_elasticity_oecd` | fiscal | PARTIAL | coef=-0.005989, p=0.859 (above α=0.1); direction inconclusive |
| `oecd_physician_density_amenable_mortality_panel` | healthcare | PARTIAL | coef=+995.7, p=0.224 (above α=0.1); direction inconclusive |
| `capacity_regulatory_quality_business_entry_complement` | institutional_quality | PARTIAL | coef=-6440, p=0.544 (above α=0.1); direction inconclusive |
| `ml_entry_barriers_informality_small_firm_productivity` | institutional_quality | PARTIAL | coef=+474.6, p=0.883 (above α=0.1); direction inconclusive |
| `bargaining_coverage_low_wage_poverty_employment_panel` | labour | PARTIAL | coef=-0.02353, p=0.241 (above α=0.1); direction inconclusive |
| `child_family_benefits_female_lfp_fertility_panel` | labour | PARTIAL | coef=+0.1572, p=0.607 (above α=0.1); direction inconclusive |
| `ml_minimum_wage_bite_youth_informality_tradeoff` | labour | PARTIAL | coef=+0.0449, p=0.294 (above α=0.1); direction inconclusive |
| `ml_service_sector_entry_female_lfp_panel` | labour | PARTIAL | coef=+2.004, p=0.48 (above α=0.1); direction inconclusive |
| `union_density_labor_share_inequality_growth_panel` | labour | PARTIAL | coef=-0.0007022, p=0.291 (above α=0.1); direction inconclusive |
| `ml_credit_boom_price_signal_bust_severity` | monetary | PARTIAL | coef=-0.01265, p=0.196 (above α=0.1); direction inconclusive |
| `ml_fdi_restriction_technology_diffusion_slowdown` | trade | PARTIAL | coef=+7.469, p=0.866 (above α=0.1); direction inconclusive |
| `wits_food_tariffs_food_price_inflation_panel` | trade | PARTIAL | coef=-0.04068, p=0.36 (above α=0.1); direction inconclusive |
