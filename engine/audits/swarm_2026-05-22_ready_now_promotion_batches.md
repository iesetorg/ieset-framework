# Swarm 2026-05-22 READY_NOW Promotion Batches

This audit records the mechanical promotion of the 85 `READY_NOW` candidates from the 200-hypothesis swarm into candidate YAML specs and steelman files.

No verdicts, run artifacts, position links, or scoreboard `covers_claims` mappings were created by this pass.

## Summary

- promoted specs: 85
- batches: 3
- batch sizes: 29, 28, 28
- status: candidate
- estimator: panel_fe first-pass triage

## Topic Split

| topic | count |
| --- | ---: |
| energy | 11 |
| fiscal | 31 |
| growth | 7 |
| healthcare | 2 |
| housing | 4 |
| institutional_quality | 2 |
| labour | 11 |
| monetary | 6 |
| trade | 10 |
| welfare_architecture | 1 |

## Batches

### Batch 1

| # | hypothesis | topic | treatment | outcome |
| ---: | --- | --- | --- | --- |
| 1 | `ml_tax_broad_base_low_rate_investment_growth_1980_2024` | fiscal | tax_revenue_share | investment_share |
| 2 | `ml_fiscal_rule_debt_service_growth_resilience` | fiscal | debt_service_ratio | real_gdp_pc_growth |
| 3 | `ml_expenditure_cap_public_investment_crowd_in` | fiscal | institutional_quality_proxy | investment_share |
| 4 | `ml_central_bank_independence_inflation_real_wage_panel` | fiscal | sound_money_proxy | cpi_inflation |
| 5 | `ml_money_growth_nominal_anchor_inflation_1960_2024` | monetary | broad_money_growth | cpi_inflation |
| 6 | `ml_financial_repression_savings_real_rate_investment` | monetary | institutional_quality_proxy | cpi_inflation |
| 7 | `ml_tariff_reduction_consumer_real_income_panel` | trade | applied_tariff_rate | real_consumption_per_capita |
| 8 | `ml_product_market_regulation_tfp_growth_oecd` | growth | product_market_regulation | tfp_index |
| 9 | `ml_expropriation_risk_private_investment_panel` | institutional_quality | institutional_quality_proxy | investment_share |
| 10 | `ml_employment_protection_youth_unemployment_duration` | labour | institutional_quality_proxy | unemployment_rate |
| 11 | `ml_carbon_pricing_command_control_cost_per_ton` | energy | carbon_price_or_policy_proxy | co2_intensity |
| 12 | `ml_rule_bound_regulation_investment_volatility` | growth | institutional_quality_proxy | investment_share |
| 13 | `ml_market_reform_package_qol_long_horizon_synth` | healthcare | trade_openness | life_expectancy |
| 14 | `redistribution_gap_bottom40_real_income_growth_oecd` | fiscal | tax_revenue_share | poverty_headcount |
| 15 | `progressive_tax_top_income_share_and_growth_oecd` | fiscal | top_marginal_income_tax_rate | investment_share |
| 16 | `public_health_spending_avoidable_mortality_panel` | fiscal | health_spending_share | mortality_rate |
| 17 | `decommodified_health_oop_spending_mortality_panel` | fiscal | health_spending_share | mortality_rate |
| 18 | `minimum_wage_bite_low_pay_poverty_employment_panel` | labour | minimum_wage_bite_proxy | poverty_headcount |
| 19 | `epl_security_youth_unemployment_dualism_panel` | labour | employment_protection_index | unemployment_rate |
| 20 | `labor_share_demand_growth_wage_led_panel` | labour | institutional_quality_proxy | labor_share |
| 21 | `shorter_hours_productivity_employment_wellbeing_panel` | labour | institutional_quality_proxy | employment_rate |
| 22 | `capital_controls_crisis_volatility_growth_panel` | growth | institutional_quality_proxy | investment_share |
| 23 | `fiscal_expansion_slack_unemployment_recovery_panel` | fiscal | government_effectiveness | unemployment_rate |
| 24 | `austerity_after_recession_hysteresis_panel` | fiscal | fiscal_balance_proxy | employment_rate |
| 25 | `policy_rate_hikes_labor_share_distribution_panel` | labour | policy_rate | labor_share |
| 26 | `fossil_subsidy_phaseout_emissions_poverty_tradeoff_panel` | energy | trade_openness | poverty_headcount |
| 27 | `renewable_capacity_employment_transition_panel` | energy | renewable_electricity_share | employment_rate |
| 28 | `material_footprint_wellbeing_decoupling_high_income_panel` | energy | institutional_quality_proxy | life_expectancy |
| 29 | `degrowth_recession_basic_needs_protection_panel` | welfare_architecture | institutional_quality_proxy | mortality_rate |

### Batch 2

| # | hypothesis | topic | treatment | outcome |
| ---: | --- | --- | --- | --- |
| 1 | `working_time_reduction_energy_use_per_capita_panel` | energy | energy_use_per_capita | employment_rate |
| 2 | `protected_land_food_security_emissions_panel` | energy | institutional_quality_proxy | co2_intensity |
| 3 | `financialization_labor_share_investment_panel` | labour | institutional_quality_proxy | labor_share |
| 4 | `capacity_stabilizers_output_loss_threshold_oecd` | fiscal | social_spending_share | unemployment_rate |
| 5 | `capacity_tax_revenue_public_goods_threshold` | fiscal | tax_revenue_share | poverty_headcount |
| 6 | `capacity_hightech_exports_government_effectiveness_interaction` | fiscal | export_product_concentration | high_tech_export_share |
| 7 | `capacity_tariff_sunset_infant_industry_upgrade` | trade | applied_tariff_rate | real_consumption_per_capita |
| 8 | `capacity_government_effectiveness_state_size_nonmonotonic` | fiscal | government_consumption_share | investment_share |
| 9 | `capacity_corruption_public_investment_leakage` | fiscal | control_of_corruption | investment_share |
| 10 | `capacity_rule_of_law_financial_depth_productive_allocation` | monetary | private_credit_gdp | tfp_index |
| 11 | `capacity_tax_administration_social_spending_poverty_elasticity` | fiscal | social_spending_share | poverty_headcount |
| 12 | `capacity_trade_liberalization_institutional_variance` | trade | applied_tariff_rate | real_consumption_per_capita |
| 13 | `capacity_education_spending_learning_threshold` | fiscal | education_spending_share | tfp_index |
| 14 | `capacity_health_spending_mortality_corruption_interaction` | fiscal | health_spending_share | mortality_rate |
| 15 | `capacity_electricity_access_regulatory_quality` | energy | regulatory_quality | real_gdp_pc_growth |
| 16 | `capacity_rnd_spending_finance_patent_productivity` | fiscal | research_and_development_intensity | resident_patents |
| 17 | `capacity_capital_market_depth_innovation_vs_volatility` | institutional_quality | private_credit_gdp | resident_patents |
| 18 | `oecd_housing_cost_overburden_consumption_drag_panel` | housing | institutional_quality_proxy | unemployment_rate |
| 19 | `oecd_rent_burden_child_poverty_panel` | housing | institutional_quality_proxy | poverty_headcount |
| 20 | `bis_house_price_growth_consumption_squeeze_panel` | housing | real_house_price_index | real_consumption_per_capita |
| 21 | `oecd_housing_cost_inequality_after_tax_panel` | fiscal | tax_revenue_share | gini_index |
| 22 | `wdi_health_spending_life_expectancy_diminishing_returns_panel` | fiscal | health_spending_share | life_expectancy |
| 23 | `wdi_out_of_pocket_health_spending_mortality_panel` | fiscal | health_spending_share | mortality_rate |
| 24 | `public_health_spending_life_expectancy_resilience_2019_2022` | fiscal | health_spending_share | life_expectancy |
| 25 | `health_spending_growth_tradeoff_panel` | fiscal | debt_service_ratio | mortality_rate |
| 26 | `oecd_epl_youth_unemployment_panel` | labour | employment_protection_index | unemployment_rate |
| 27 | `oecd_minimum_wage_bite_low_education_unemployment_panel` | labour | minimum_wage_bite_proxy | unemployment_rate |
| 28 | `ilostat_services_growth_female_lfp_panel` | labour | services_value_added_share | employment_rate |

### Batch 3

| # | hypothesis | topic | treatment | outcome |
| ---: | --- | --- | --- | --- |
| 1 | `oecd_union_density_wage_dispersion_employment_tradeoff` | labour | trade_openness | employment_rate |
| 2 | `oecd_education_spending_human_capital_gain_panel` | fiscal | education_spending_share | real_gdp_pc_growth |
| 3 | `wdi_tertiary_attainment_hightech_exports_panel` | trade | trade_openness | high_tech_export_share |
| 4 | `pwt_human_capital_tfp_growth_panel` | growth | human_capital_index | tfp_index |
| 5 | `eurostat_industrial_power_price_manufacturing_share_panel` | energy | institutional_quality_proxy | real_gdp_pc_growth |
| 6 | `owid_fossil_subsidy_energy_intensity_panel` | energy | fossil_fuel_consumption_subsidies | real_consumption_per_capita |
| 7 | `nuclear_share_power_price_volatility_panel` | energy | nuclear_electricity_share | co2_intensity |
| 8 | `energy_use_life_expectancy_saturation_threshold_panel` | healthcare | energy_use_per_capita | life_expectancy |
| 9 | `wits_tariff_cuts_import_variety_consumption_panel` | trade | applied_tariff_rate | real_consumption_per_capita |
| 10 | `wits_export_product_diversification_resilience_panel` | trade | export_product_concentration | real_gdp_pc_growth |
| 11 | `wits_tariff_protection_manufacturing_upgrade_panel` | trade | applied_tariff_rate | high_tech_export_share |
| 12 | `trade_openness_unemployment_volatility_panel` | trade | trade_openness | unemployment_rate |
| 13 | `bis_reer_appreciation_export_variety_panel` | trade | real_effective_exchange_rate | real_gdp_pc_growth |
| 14 | `tax_revenue_public_investment_growth_panel` | fiscal | tax_revenue_share | investment_share |
| 15 | `government_consumption_private_investment_drag_panel` | fiscal | debt_service_ratio | real_consumption_per_capita |
| 16 | `oecd_socx_poverty_reduction_per_spending_point_panel` | fiscal | social_spending_share | poverty_headcount |
| 17 | `fiscal_balance_real_rate_growth_interaction_panel` | fiscal | fiscal_balance_proxy | cpi_inflation |
| 18 | `bis_credit_gap_house_price_unemployment_lag_panel` | housing | credit_gap | unemployment_rate |
| 19 | `bis_household_dsr_policy_rate_consumption_slowdown_panel` | monetary | debt_service_ratio | real_consumption_per_capita |
| 20 | `fred_m2_asset_price_cpi_divergence_us_panel` | monetary | broad_money_growth | cpi_inflation |
| 21 | `bis_low_policy_rate_credit_gap_asset_cycle_panel` | monetary | credit_gap | cpi_inflation |
| 22 | `wipo_resident_patenting_tfp_followthrough_panel` | growth | resident_patents | tfp_index |
| 23 | `rnd_spending_patent_intensity_panel` | fiscal | research_and_development_intensity | resident_patents |
| 24 | `hightech_exports_product_concentration_growth_panel` | trade | export_product_concentration | high_tech_export_share |
| 25 | `governance_rnd_hightech_return_panel` | fiscal | research_and_development_intensity | high_tech_export_share |
| 26 | `agricultural_productivity_poverty_reduction_panel` | growth | agriculture_value_added_share | mortality_rate |
| 27 | `agriculture_employment_transition_productivity_panel` | growth | services_value_added_share | employment_rate |
| 28 | `forest_loss_agricultural_growth_tradeoff_panel` | energy | trade_openness | poverty_headcount |
