# Throughput Scoreboard Conversion Audit

Generated: 2026-05-13

## Methodology Gate

- Raw verdict throughput is not scoreboard conversion. Conversion requires a real verdict, non-ambiguous interpretation, claim mapping, and no duplicate broad-panel QA hold.
- `scoreboard_ready_existing_mapping`: safe to include in the next scoreboard recompute, subject to normal validation.
- `needs_position_claim_mapping` / `needs_hypothesis_covers_claims`: evidence exists, but the school-claim mapping is incomplete.
- `hold_*`: evidence exists, but interpretation or duplicate broad-panel QA must be fixed before scoreboard conversion.
- `repair_data_or_design`: not a verdict-bearing result.

## Summary

- batch_files: ['engine/audits/monthly_hypothesis_throughput_kickoff_2026-05-12.md', 'engine/audits/monthly_hypothesis_throughput_batch_02_2026-05-12.md', 'engine/audits/monthly_hypothesis_throughput_batch_03_2026-05-12.md', 'engine/audits/monthly_hypothesis_throughput_batch_04_2026-05-12.md']
- hypotheses_reviewed: 129
- verdict_counts: {'inconclusive': 21, 'partial': 41, 'refuted': 25, 'supported': 42}
- conversion_counts: {'repair_data_or_design': 21, 'hold_interpretation_qa': 29, 'needs_position_claim_mapping': 3, 'scoreboard_ready_existing_mapping': 56, 'hold_duplicate_broad_panel_qa': 18, 'hold_broad_panel_upgrade': 2}
- qa_flag_counts: {'associational_panel': 89, 'direction_inconclusive': 20, 'zero_effect_partial': 6, 'broad_scope': 17, 'duplicate_fingerprint': 18, 'direction_ambiguous': 8}
- duplicate_fingerprint_groups: 6

## Conversion Buckets

| bucket | count |
| --- | ---: |
| `hold_broad_panel_upgrade` | 2 |
| `hold_duplicate_broad_panel_qa` | 18 |
| `hold_interpretation_qa` | 29 |
| `needs_position_claim_mapping` | 3 |
| `repair_data_or_design` | 21 |
| `scoreboard_ready_existing_mapping` | 56 |

## Records

| hypothesis | verdict | evidence | links | covers | conversion bucket | QA flags |
| --- | --- | --- | ---: | ---: | --- | --- |
| `industrial_concentration_labour_share_link` | inconclusive | associational | 1 | 1 | `repair_data_or_design` | associational_panel |
| `us_eu_gdp_per_capita_divergence_policy_causes` | partial | associational | 6 | 6 | `hold_interpretation_qa` | direction_inconclusive |
| `federal_minimum_wage_employment_meta` | inconclusive | associational | 1 | 1 | `repair_data_or_design` | - |
| `oecd_low_education_unemployment_minimum_wage_bite` | refuted | associational | 0 | 0 | `needs_position_claim_mapping` | - |
| `bls_qcew_county_food_service_minimum_wage_growth` | refuted | associational | 0 | 0 | `needs_position_claim_mapping` | - |
| `china_renewables_global_learning_curve_spillover` | refuted | descriptive | 3 | 3 | `scoreboard_ready_existing_mapping` | - |
| `ira_2022_clean_energy_investment_decomposition` | inconclusive | causal | 0 | 0 | `repair_data_or_design` | - |
| `financial_negative_rates_eurozone_2014_2022` | inconclusive | descriptive | 0 | 0 | `repair_data_or_design` | - |
| `eurozone_austerity_distributional_incidence` | inconclusive | associational | 10 | 10 | `repair_data_or_design` | - |
| `child_benefit_expansion_child_poverty_effect` | inconclusive | associational | 1 | 1 | `repair_data_or_design` | - |
| `latam_extra_capital_account_openness_panel_1990_2024` | partial | associational | 0 | 0 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `liberal_capital_account_openness_growth_premium_panel` | partial | associational | 0 | 0 | `hold_interpretation_qa` | zero_effect_partial, associational_panel |
| `capital_account_openness_institutional_threshold` | partial | causal | 0 | 0 | `hold_interpretation_qa` | broad_scope, direction_inconclusive |
| `market_order_capital_account_openness_fdi_inflows_share_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_capital_account_openness_gdp_pc_growth_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_capital_account_openness_high_tech_exports_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_capital_account_openness_private_investment_share_panel` | refuted | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_fiscal_balance_gdp_pc_growth_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_fiscal_balance_private_investment_share_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_fiscal_balance_gross_savings_share_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_fiscal_balance_private_credit_depth_panel` | refuted | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_public_debt_gdp_pc_growth_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_public_debt_private_investment_share_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_public_debt_gross_savings_share_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_public_debt_private_credit_depth_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_consumption_gdp_pc_growth_panel` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_government_consumption_private_investment_share_panel` | partial | associational | 3 | 3 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_consumption_gross_savings_share_panel` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `market_order_government_consumption_manufacturing_share_panel` | partial | associational | 3 | 3 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_effectiveness_gdp_pc_growth_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_effectiveness_private_investment_share_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_effectiveness_gross_savings_share_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `market_order_government_effectiveness_manufacturing_share_panel` | partial | associational | 4 | 4 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `oecd_product_market_deregulation_tfp_panel` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `unemployment_benefit_generosity_employment_drag` | partial | associational | 8 | 8 | `hold_interpretation_qa` | broad_scope, direction_inconclusive, associational_panel |
| `government_spending_tfp_drag_panel` | partial | associational | 0 | 0 | `hold_interpretation_qa` | broad_scope, direction_inconclusive, associational_panel |
| `flat_tax_reform_growth_panel` | partial | associational | 0 | 0 | `hold_interpretation_qa` | direction_inconclusive, associational_panel |
| `mortgage_market_liberalisation_homeownership_panel` | partial | associational | 0 | 0 | `hold_interpretation_qa` | broad_scope, direction_inconclusive, associational_panel |
| `privatisation_transition_tfp_panel` | inconclusive | associational | 5 | 5 | `repair_data_or_design` | associational_panel |
| `business_dynamism_frontier_income_growth` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `price_signal_integrity_qol_panel` | refuted | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `platform_competition_dissipates_monopoly_rent` | refuted | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `intervention_reversal_qol_loss_1980_2024` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `latam_resource_nationalisation_social_outcome_tradeoff` | partial | associational | 10 | 10 | `hold_interpretation_qa` | direction_ambiguous, associational_panel |
| `price_controls_food_output_decline_panel` | refuted | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `caribbean_climate_resilience_panel_1990_2024` | inconclusive | causal | 0 | 0 | `repair_data_or_design` | - |
| `gfc_household_debt_wage_stagnation_link` | partial | associational | 10 | 10 | `hold_interpretation_qa` | direction_ambiguous, associational_panel |
| `market_reform_female_education` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `asia_bangladesh_apparel_growth_1985_2024` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `spectrum_auction_vs_administrative_allocation_telecom` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `sea_singapore_fta_cascade_post_2014` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `banking_crisis_schularick_taylor_credit_boom_panel_post1980` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `japan_miti_success_then_stagnation_panel` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `china_soe_vs_cee_privatised_growth` | inconclusive | associational | 8 | 8 | `repair_data_or_design` | associational_panel |
| `generic_substitution_mandate_savings_no_harm` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `demo_canada_points_system_immigration` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `sea_indonesia_jokowi_infrastructure_2014_2024` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `bank_state_ownership_credit_misallocation` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `strong_union_labour_law_youth_unemployment_south_europe` | refuted | causal | 17 | 17 | `scoreboard_ready_existing_mapping` | - |
| `market_income_school_completion` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `india_extra_modi_era_growth_2014_2024` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `demo_life_expectancy_lfp_panel` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `tax_simplicity_disposable_income_growth` | supported | associational | 0 | 0 | `hold_broad_panel_upgrade` | broad_scope, associational_panel |
| `crony_capitalism_not_market_freedom` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `market_institution_duration_qol_persistence` | refuted | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `qol_anomaly_weight_broad_scope_test` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `occupational_licensing_income_mobility` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `demo_marriage_age_fertility_growth` | partial | associational | 0 | 0 | `hold_interpretation_qa` | direction_inconclusive |
| `firm_entry_rate_long_run_productivity` | supported | associational | 11 | 11 | `scoreboard_ready_existing_mapping` | associational_panel |
| `net_migration_revealed_preference_market_institutions` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `hayek_regulatory_uncertainty_investment_chilling` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `medical_migration_market_opportunity` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `economic_freedom_corruption_decline` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | - |
| `bukele_fiscal_trajectory_tax_cuts_imf_2019_2024` | refuted | causal | 17 | 17 | `scoreboard_ready_existing_mapping` | broad_scope |
| `market_reform_inflation_adjusted_wages` | refuted | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `market_freedom_consumption_pc_1970_2024` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `regulatory_transparency_investment` | partial | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | - |
| `market_governance_qol_broad_scope` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `debt_overhang_private_investment_30yr` | supported | causal | 3 | 3 | `scoreboard_ready_existing_mapping` | broad_scope |
| `sea_thailand_2014_coup_tourism_shock` | refuted | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `price_signal_distortion_capital_misallocation` | partial | associational | 7 | 7 | `hold_interpretation_qa` | broad_scope, direction_inconclusive, associational_panel |
| `public_procurement_innovation_conditions` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `intervention_intensity_qol_volatility_1970_2024` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | broad_scope, associational_panel, duplicate_fingerprint |
| `market_entry_uniform_code_productivity` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `female_lfp_market_opportunity` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `procurement_competition_corruption` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `labor_reform_real_wage_growth` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `gm_crop_adoption_yield_convergence` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `regulatory_predictability_cross_sector_investment` | refuted | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `frontier_income_volatility_state_allocation` | refuted | associational | 11 | 11 | `scoreboard_ready_existing_mapping` | associational_panel |
| `campaign_favoritism_subsidy_allocation` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `health_savings_account_preventive_spending` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `gfc_balance_sheet_recession_post_2008_household_dual_mandate` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `housing_tax_distortion_mobility` | refuted | associational | 0 | 0 | `hold_broad_panel_upgrade` | broad_scope, associational_panel |
| `licensing_discretion_bribery` | supported | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | associational_panel, duplicate_fingerprint |
| `dialysis_market_competition_outcome_quality` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `sea_philippines_bpo_industrial_policy_2005_2024` | supported | associational | 3 | 3 | `scoreboard_ready_existing_mapping` | associational_panel |
| `venture_capital_market_depth_innovation` | refuted | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `banking_crisis_laeven_valencia_predictors_panel` | supported | associational | 4 | 4 | `scoreboard_ready_existing_mapping` | associational_panel |
| `CBDC_design_privacy_tradeoff` | partial | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | zero_effect_partial, associational_panel, duplicate_fingerprint |
| `abenomics_monetary_fiscal_coordination_effect` | inconclusive | associational | 1 | 1 | `repair_data_or_design` | - |
| `absolute_decoupling_global_material_throughput` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `active_labour_market_policy_conditionality_works` | partial | associational | 8 | 8 | `hold_duplicate_broad_panel_qa` | zero_effect_partial, associational_panel, duplicate_fingerprint |
| `africa_botswana_diamond_dependency_post_2014` | partial | causal | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `africa_ethiopia_gerd_economic_effect_2011_2024` | partial | causal | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `africa_ethiopia_tigray_war_economic_collapse_2020_2022` | partial | causal | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `africa_ghana_imf_program_2022_debt_distress` | partial | causal | 0 | 0 | `hold_interpretation_qa` | direction_ambiguous |
| `africa_kenya_mpesa_digital_payments_formalisation_2007_2024` | inconclusive | causal | 0 | 0 | `repair_data_or_design` | - |
| `africa_mauritius_export_zone_model_1980_2024` | partial | causal | 0 | 0 | `hold_interpretation_qa` | direction_ambiguous |
| `africa_nigeria_fuel_subsidy_removal_2023` | inconclusive | causal | 0 | 0 | `repair_data_or_design` | - |
| `africa_nigeria_naira_redesign_2023_cash_crisis` | partial | causal | 0 | 0 | `hold_interpretation_qa` | direction_ambiguous |
| `africa_rwanda_post_genocide_growth_model_1995_2024` | partial | causal | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `africa_south_africa_load_shedding_manufacturing_2007_2024` | partial | causal | 0 | 0 | `needs_position_claim_mapping` | broad_scope |
| `africa_ssa_post_covid_recovery_divergence_2020_2024` | refuted | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | associational_panel |
| `agricultural_export_ban_price_instability` | partial | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | zero_effect_partial, associational_panel, duplicate_fingerprint |
| `agricultural_trade_liberalisation_food_security` | partial | associational | 0 | 0 | `hold_duplicate_broad_panel_qa` | zero_effect_partial, associational_panel, duplicate_fingerprint |
| `albania_growth_health_services_shift_1990_2023` | supported | canonical_case_multi_metric | 1 | 1 | `scoreboard_ready_existing_mapping` | - |
| `apprenticeship_employer_chamber_quality` | partial | associational | 8 | 8 | `hold_duplicate_broad_panel_qa` | zero_effect_partial, associational_panel, duplicate_fingerprint |
| `argentina_cepo_lift_2015_fx_inflation_reserves` | supported | canonical_case_multi_metric | 1 | 1 | `scoreboard_ready_existing_mapping` | - |
| `argentina_default_collapse_output_effects` | partial | associational | 3 | 3 | `hold_interpretation_qa` | direction_ambiguous |
| `argentina_fx_obligation_inflation_mechanism` | supported | associational | 2 | 2 | `scoreboard_ready_existing_mapping` | - |
| `argentina_institutional_instability_decline` | inconclusive | canonical_case_multi_metric | 1 | 1 | `repair_data_or_design` | - |
| `argentina_paso_2019_fx_reserves_inflation_base_money_lag` | supported | canonical_case_multi_metric | 1 | 1 | `scoreboard_ready_existing_mapping` | - |
| `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023` | partial | causal | 17 | 17 | `scoreboard_ready_existing_mapping` | - |
| `armenia_growth_health_services_shift_1990_2023` | supported | canonical_case_multi_metric | 1 | 1 | `scoreboard_ready_existing_mapping` | - |
| `asia_japan_abenomics_retrospective_2013_2023` | supported | descriptive | 3 | 3 | `scoreboard_ready_existing_mapping` | - |
| `asia_korea_chaebol_reform_2017_2024` | partial | descriptive | 0 | 0 | `hold_interpretation_qa` | broad_scope, direction_ambiguous |
| `asia_pakistan_imf_programme_cycle_1988_2024` | inconclusive | associational | 0 | 0 | `repair_data_or_design` | associational_panel |
| `asia_sri_lanka_default_2022_imf_2023` | partial | descriptive | 0 | 0 | `hold_interpretation_qa` | direction_ambiguous |
