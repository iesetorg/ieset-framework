# Swarm 2026-05-22 READY_NOW Run Results

This audit records the first-pass generic `panel_fe` execution of the 85 promoted `READY_NOW` candidates from the 200-hypothesis swarm.

These are triage verdicts only: no scoreboard mappings or claim links were added in this pass.

## Summary

- hypotheses attempted: 85
- diagnostics written: 85
- supported: 9
- refuted: 22
- partial: 53
- inconclusive_data_pending: 1
- runner repair: `scripts/run_panel_fe.py` now treats `GLOBAL` as an all-country sample instead of a literal country filter
- promotion repair: patent/R&D/financial-depth specs no longer use the same patent variable as both treatment and outcome

## Topic By Verdict

| topic | supported | refuted | partial | inconclusive | total |
| --- | ---: | ---: | ---: | ---: | ---: |
| energy | 0 | 3 | 8 | 0 | 11 |
| fiscal | 7 | 7 | 17 | 0 | 31 |
| growth | 0 | 3 | 3 | 1 | 7 |
| healthcare | 0 | 0 | 2 | 0 | 2 |
| housing | 0 | 1 | 3 | 0 | 4 |
| institutional_quality | 0 | 0 | 2 | 0 | 2 |
| labour | 0 | 4 | 7 | 0 | 11 |
| monetary | 2 | 3 | 1 | 0 | 6 |
| trade | 0 | 1 | 9 | 0 | 10 |
| welfare_architecture | 0 | 0 | 1 | 0 | 1 |

## Inconclusive

| hypothesis | topic | reason |
| --- | --- | --- |
| `ml_product_market_regulation_tfp_growth_oecd` | growth | treatment 'product_market_regulation' has no within-country variation under country fixed effects |

## Verdict Inventory

| hypothesis | topic | verdict | reason |
| --- | --- | --- | --- |
| `capacity_tax_administration_social_spending_poverty_elasticity` | fiscal | SUPPORTED | coef=-1.063e-06 (sign matches claim -), p=0.0346 |
| `capacity_tax_revenue_public_goods_threshold` | fiscal | SUPPORTED | coef=-0.3872 (sign matches claim -), p=0.0015 |
| `governance_rnd_hightech_return_panel` | fiscal | SUPPORTED | coef=+3.443 (sign matches claim +), p=0.00454 |
| `ml_central_bank_independence_inflation_real_wage_panel` | fiscal | SUPPORTED | coef=-7.504 (sign matches claim -), p=1.88e-05 |
| `ml_fiscal_rule_debt_service_growth_resilience` | fiscal | SUPPORTED | coef=-0.196 (sign matches claim -), p=7.84e-11 |
| `oecd_socx_poverty_reduction_per_spending_point_panel` | fiscal | SUPPORTED | coef=-1.106e-06 (sign matches claim -), p=0.0242 |
| `wdi_out_of_pocket_health_spending_mortality_panel` | fiscal | SUPPORTED | coef=+1.089 (sign matches claim +), p=0.0605 |
| `fred_m2_asset_price_cpi_divergence_us_panel` | monetary | SUPPORTED | coef=+0.5035 (sign matches claim +), p=0.000521 |
| `ml_financial_repression_savings_real_rate_investment` | monetary | SUPPORTED | coef=-3.136 (sign matches claim -), p=0.00633 |
| `forest_loss_agricultural_growth_tradeoff_panel` | energy | REFUTED | coef=+0.08003 (sign opposite claim -), p=0.0015 |
| `fossil_subsidy_phaseout_emissions_poverty_tradeoff_panel` | energy | REFUTED | coef=+0.08003 (sign opposite claim -), p=0.0015 |
| `ml_carbon_pricing_command_control_cost_per_ton` | energy | REFUTED | coef=+1 (sign opposite claim -), p=0 |
| `capacity_health_spending_mortality_corruption_interaction` | fiscal | REFUTED | coef=+1.089 (sign opposite claim -), p=0.0605 |
| `capacity_stabilizers_output_loss_threshold_oecd` | fiscal | REFUTED | coef=+4.19e-07 (sign opposite claim -), p=0.0769 |
| `decommodified_health_oop_spending_mortality_panel` | fiscal | REFUTED | coef=+1.089 (sign opposite claim -), p=0.0605 |
| `government_consumption_private_investment_drag_panel` | fiscal | REFUTED | coef=+176.6 (sign opposite claim -), p=0.016 |
| `public_health_spending_avoidable_mortality_panel` | fiscal | REFUTED | coef=+1.089 (sign opposite claim -), p=0.0605 |
| `public_health_spending_life_expectancy_resilience_2019_2022` | fiscal | REFUTED | coef=-0.2114 (sign opposite claim +), p=0.0181 |
| `redistribution_gap_bottom40_real_income_growth_oecd` | fiscal | REFUTED | coef=-0.1805 (sign opposite claim +), p=0.061 |
| `agricultural_productivity_poverty_reduction_panel` | growth | REFUTED | coef=+1.002 (sign opposite claim -), p=0.00181 |
| `pwt_human_capital_tfp_growth_panel` | growth | REFUTED | coef=-0.2874 (sign opposite claim +), p=0.00946 |
| `wipo_resident_patenting_tfp_followthrough_panel` | growth | REFUTED | coef=-2.875e-07 (sign opposite claim +), p=1.7e-09 |
| `bis_house_price_growth_consumption_squeeze_panel` | housing | REFUTED | coef=+41.2 (sign opposite claim -), p=0.0129 |
| `epl_security_youth_unemployment_dualism_panel` | labour | REFUTED | coef=-3.145 (sign opposite claim +), p=0.00264 |
| `financialization_labor_share_investment_panel` | labour | REFUTED | coef=+0.009192 (sign opposite claim -), p=0.0612 |
| `labor_share_demand_growth_wage_led_panel` | labour | REFUTED | coef=+0.009192 (sign opposite claim -), p=0.0612 |
| `oecd_epl_youth_unemployment_panel` | labour | REFUTED | coef=-3.145 (sign opposite claim +), p=0.00264 |
| `bis_household_dsr_policy_rate_consumption_slowdown_panel` | monetary | REFUTED | coef=+176.6 (sign opposite claim -), p=0.016 |
| `capacity_rule_of_law_financial_depth_productive_allocation` | monetary | REFUTED | coef=-0.001099 (sign opposite claim +), p=0.00632 |
| `ml_money_growth_nominal_anchor_inflation_1960_2024` | monetary | REFUTED | coef=+0.5035 (sign opposite claim -), p=0.000521 |
| `wits_tariff_protection_manufacturing_upgrade_panel` | trade | REFUTED | coef=-0.1616 (sign opposite claim +), p=0.000146 |
| `capacity_electricity_access_regulatory_quality` | energy | PARTIAL | coef=-0.469, p=0.388 (above α=0.1); direction inconclusive |
| `eurostat_industrial_power_price_manufacturing_share_panel` | energy | PARTIAL | coef=+0.2102, p=0.443 (above α=0.1); direction inconclusive |
| `material_footprint_wellbeing_decoupling_high_income_panel` | energy | PARTIAL | coef=+0.2599, p=0.189 (above α=0.1); direction inconclusive |
| `nuclear_share_power_price_volatility_panel` | energy | PARTIAL | coef=-0.001484, p=0.143 (above α=0.1); direction inconclusive |
| `owid_fossil_subsidy_energy_intensity_panel` | energy | PARTIAL | coef=+7.993e-09, p=0.666 (above α=0.1); direction inconclusive |
| `protected_land_food_security_emissions_panel` | energy | PARTIAL | coef=-0.01893, p=0.228 (above α=0.1); direction inconclusive |
| `renewable_capacity_employment_transition_panel` | energy | PARTIAL | coef=+0.01962, p=0.243 (above α=0.1); direction inconclusive |
| `working_time_reduction_energy_use_per_capita_panel` | energy | PARTIAL | coef=+1.184e-05, p=0.97 (above α=0.1); direction inconclusive |
| `austerity_after_recession_hysteresis_panel` | fiscal | PARTIAL | coef=+0.004349, p=0.479 (above α=0.1); direction inconclusive |
| `capacity_corruption_public_investment_leakage` | fiscal | PARTIAL | coef=-0.2481, p=0.811 (above α=0.1); direction inconclusive |
| `capacity_education_spending_learning_threshold` | fiscal | PARTIAL | coef=-0.0001334, p=0.985 (above α=0.1); direction inconclusive |
| `capacity_government_effectiveness_state_size_nonmonotonic` | fiscal | PARTIAL | coef=+0.06252, p=0.278 (above α=0.1); direction inconclusive |
| `capacity_hightech_exports_government_effectiveness_interaction` | fiscal | PARTIAL | coef=+1.8, p=0.639 (above α=0.1); direction inconclusive |
| `capacity_rnd_spending_finance_patent_productivity` | fiscal | PARTIAL | coef=+6.687e+04, p=0.185 (above α=0.1); direction inconclusive |
| `fiscal_balance_real_rate_growth_interaction_panel` | fiscal | PARTIAL | coef=+0.02846, p=0.172 (above α=0.1); direction inconclusive |
| `fiscal_expansion_slack_unemployment_recovery_panel` | fiscal | PARTIAL | coef=-0.5558, p=0.203 (above α=0.1); direction inconclusive |
| `health_spending_growth_tradeoff_panel` | fiscal | PARTIAL | coef=+0.03855, p=0.698 (above α=0.1); direction inconclusive |
| `ml_expenditure_cap_public_investment_crowd_in` | fiscal | PARTIAL | coef=+0.5618, p=0.249 (above α=0.1); direction inconclusive |
| `ml_tax_broad_base_low_rate_investment_growth_1980_2024` | fiscal | PARTIAL | coef=+0.01529, p=0.654 (above α=0.1); direction inconclusive |
| `oecd_education_spending_human_capital_gain_panel` | fiscal | PARTIAL | coef=-0.3146, p=0.346 (above α=0.1); direction inconclusive |
| `oecd_housing_cost_inequality_after_tax_panel` | fiscal | PARTIAL | coef=-0.06882, p=0.469 (above α=0.1); direction inconclusive |
| `progressive_tax_top_income_share_and_growth_oecd` | fiscal | PARTIAL | coef=-0.03954, p=0.605 (above α=0.1); direction inconclusive |
| `rnd_spending_patent_intensity_panel` | fiscal | PARTIAL | coef=+6.687e+04, p=0.185 (above α=0.1); direction inconclusive |
| `tax_revenue_public_investment_growth_panel` | fiscal | PARTIAL | coef=+0.01529, p=0.654 (above α=0.1); direction inconclusive |
| `wdi_health_spending_life_expectancy_diminishing_returns_panel` | fiscal | PARTIAL | coef=+0.06529, p=0.471 (above α=0.1); direction inconclusive |
| `agriculture_employment_transition_productivity_panel` | growth | PARTIAL | coef=+0.01781, p=0.497 (above α=0.1); direction inconclusive |
| `capital_controls_crisis_volatility_growth_panel` | growth | PARTIAL | coef=+0.5618, p=0.249 (above α=0.1); direction inconclusive |
| `ml_rule_bound_regulation_investment_volatility` | growth | PARTIAL | coef=+0.5618, p=0.249 (above α=0.1); direction inconclusive |
| `energy_use_life_expectancy_saturation_threshold_panel` | healthcare | PARTIAL | coef=-0.0001106, p=0.244 (above α=0.1); direction inconclusive |
| `ml_market_reform_package_qol_long_horizon_synth` | healthcare | PARTIAL | coef=-0.004227, p=0.104 (above α=0.1); direction inconclusive |
| `bis_credit_gap_house_price_unemployment_lag_panel` | housing | PARTIAL | coef=-0.01265, p=0.196 (above α=0.1); direction inconclusive |
| `oecd_housing_cost_overburden_consumption_drag_panel` | housing | PARTIAL | coef=-0.5672, p=0.139 (above α=0.1); direction inconclusive |
| `oecd_rent_burden_child_poverty_panel` | housing | PARTIAL | coef=-0.4774, p=0.18 (above α=0.1); direction inconclusive |
| `capacity_capital_market_depth_innovation_vs_volatility` | institutional_quality | PARTIAL | coef=+357.3, p=0.214 (above α=0.1); direction inconclusive |
| `ml_expropriation_risk_private_investment_panel` | institutional_quality | PARTIAL | coef=+0.5618, p=0.249 (above α=0.1); direction inconclusive |
| `ilostat_services_growth_female_lfp_panel` | labour | PARTIAL | coef=+0.01781, p=0.497 (above α=0.1); direction inconclusive |
| `minimum_wage_bite_low_pay_poverty_employment_panel` | labour | PARTIAL | coef=-0.03318, p=0.245 (above α=0.1); direction inconclusive |
| `ml_employment_protection_youth_unemployment_duration` | labour | PARTIAL | coef=-0.2779, p=0.204 (above α=0.1); direction inconclusive |
| `oecd_minimum_wage_bite_low_education_unemployment_panel` | labour | PARTIAL | coef=+0.0449, p=0.294 (above α=0.1); direction inconclusive |
| `oecd_union_density_wage_dispersion_employment_tradeoff` | labour | PARTIAL | coef=-0.008017, p=0.724 (above α=0.1); direction inconclusive |
| `policy_rate_hikes_labor_share_distribution_panel` | labour | PARTIAL | coef=+0.0007628, p=0.384 (above α=0.1); direction inconclusive |
| `shorter_hours_productivity_employment_wellbeing_panel` | labour | PARTIAL | coef=+0.4753, p=0.133 (above α=0.1); direction inconclusive |
| `bis_low_policy_rate_credit_gap_asset_cycle_panel` | monetary | PARTIAL | coef=+0.01886, p=0.125 (above α=0.1); direction inconclusive |
| `bis_reer_appreciation_export_variety_panel` | trade | PARTIAL | coef=-0.008386, p=0.208 (above α=0.1); direction inconclusive |
| `capacity_tariff_sunset_infant_industry_upgrade` | trade | PARTIAL | coef=+7.994, p=0.354 (above α=0.1); direction inconclusive |
| `capacity_trade_liberalization_institutional_variance` | trade | PARTIAL | coef=+7.994, p=0.354 (above α=0.1); direction inconclusive |
| `hightech_exports_product_concentration_growth_panel` | trade | PARTIAL | coef=+1.8, p=0.639 (above α=0.1); direction inconclusive |
| `ml_tariff_reduction_consumer_real_income_panel` | trade | PARTIAL | coef=+7.994, p=0.354 (above α=0.1); direction inconclusive |
| `trade_openness_unemployment_volatility_panel` | trade | PARTIAL | coef=-0.006867, p=0.112 (above α=0.1); direction inconclusive |
| `wdi_tertiary_attainment_hightech_exports_panel` | trade | PARTIAL | coef=-0.01952, p=0.512 (above α=0.1); direction inconclusive |
| `wits_export_product_diversification_resilience_panel` | trade | PARTIAL | coef=-1.849, p=0.152 (above α=0.1); direction inconclusive |
| `wits_tariff_cuts_import_variety_consumption_panel` | trade | PARTIAL | coef=+7.994, p=0.354 (above α=0.1); direction inconclusive |
| `degrowth_recession_basic_needs_protection_panel` | welfare_architecture | PARTIAL | coef=-2.469, p=0.189 (above α=0.1); direction inconclusive |
| `ml_product_market_regulation_tfp_growth_oecd` | growth | INCONCLUSIVE_DATA_PENDING | treatment 'product_market_regulation' has no within-country variation under country fixed effects |
