# School Coverage Run Queue

Generated: 2026-05-04

## Methodology Gate

- This queue ranks already-linked pending hypotheses by coverage unlocked for under-covered schools.
- It does not change verdicts, school predictions, polarity, or net scores.
- The fastest fair path is to run or repair pending hypotheses before inventing new links.
- New hypotheses are allowed only where linked coverage is still below the selected floor after the pending queue is exhausted.

## Summary

- Under-covered schools: 16
- Pending candidates with coverage benefit: 55
- Top blocker types: needs_successful_rerun=53, needs_run_dir=2
- Linked gap remaining after pending runs: 195
- Tested gap remaining after exhausting pending runs: 195

## Highest-Leverage Queue

| rank | hypothesis | score | schools helped | axis | blocker |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | `intergenerational_mobility_cross_country` | 18.497 | 16 (`austrian`, `chicago_monetarism`, `empirical_pragmatist`, `social_democratic`, `developmentalism` +11) | `fiscal.tax_progressivity` | needs_successful_rerun |
| 2 | `minimum_wage_above_median_employment_teen_effects` | 18.497 | 16 (`austrian`, `chicago_monetarism`, `empirical_pragmatist`, `social_democratic`, `developmentalism` +11) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 3 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | 18.497 | 16 (`austrian`, `chicago_monetarism`, `empirical_pragmatist`, `social_democratic`, `developmentalism` +11) | `regulatory.energy_supply_security` | needs_successful_rerun |
| 4 | `wealth_tax_capital_flight_revenue_yield_gap` | 18.497 | 16 (`austrian`, `chicago_monetarism`, `empirical_pragmatist`, `social_democratic`, `developmentalism` +11) | `fiscal.tax_capital` | needs_successful_rerun |
| 5 | `tax_inequality_korea_progressive_turn_2017_2020` | 10.428 | 9 (`post_keynesian`, `mmt`, `new_keynesian`, `degrowth`, `market_socialist` +4) | `fiscal.tax_progressivity` | needs_successful_rerun |
| 6 | `financial_liberalisation_crisis_risk` | 9.269 | 8 (`post_keynesian`, `mmt`, `degrowth`, `market_socialist`, `marxian` +3) | `regulatory.financial_deregulation` | needs_successful_rerun |
| 7 | `industrial_policy_high_governance_success` | 9.228 | 8 (`austrian`, `chicago_monetarism`, `empirical_pragmatist`, `social_democratic`, `developmentalism` +3) | `regulatory.trade_openness` | needs_successful_rerun |
| 8 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | 8.110 | 7 (`mmt`, `degrowth`, `market_socialist`, `marxian`, `eco_socialist` +2) | `fiscal.sectoral_subsidy` | needs_successful_rerun |
| 9 | `china_renewables_industrial_policy_learning_curve` | 8.110 | 7 (`mmt`, `degrowth`, `market_socialist`, `marxian`, `eco_socialist` +2) | `fiscal.sectoral_subsidy` | needs_successful_rerun |
| 10 | `natural_monopoly_private_failure` | 8.110 | 7 (`mmt`, `degrowth`, `market_socialist`, `marxian`, `eco_socialist` +2) | `institutional.property_rights` | needs_successful_rerun |
| 11 | `fossil_subsidy_persistence_private_ownership_link` | 4.634 | 4 (`mmt`, `degrowth`, `market_socialist`, `eco_socialist`) | `fiscal.sectoral_subsidy` | needs_successful_rerun |
| 12 | `macron_labour_tax_employment_distribution` | 3.490 | 3 (`empirical_pragmatist`, `social_democratic`, `new_keynesian`) | `fiscal.tax_corporate` | needs_successful_rerun |
| 13 | `austerity_output_recovery_tradeoff` | 3.483 | 3 (`social_democratic`, `post_keynesian`, `new_keynesian`) | `fiscal.spending_level` | needs_successful_rerun |
| 14 | `welfare_architecture_market_openness_nordic` | 3.421 | 3 (`empirical_pragmatist`, `social_democratic`, `ordoliberal`) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 15 | `rent_control_reduces_housing_supply_and_quality` | 2.324 | 2 (`chicago_monetarism`, `democratic_socialist`) | `regulatory.product_market_competition` | needs_successful_rerun |
| 16 | `industrial_policy_semiconductor_chips_act_effectiveness` | 2.324 | 2 (`empirical_pragmatist`, `developmentalism`) | `fiscal.sectoral_subsidy` | needs_successful_rerun |
| 17 | `frontier_tfp_market_liberal_panel_1970_2024` | 2.248 | 2 (`institutionalism`, `ordoliberal`) | `institutional.property_rights` | needs_successful_rerun |
| 18 | `fiat_expansion_erodes_currency_purchasing_power_long_run` | 1.166 | 1 (`austrian`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 19 | `friedman_schwartz_great_depression_monetary_cause` | 1.166 | 1 (`chicago_monetarism`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 20 | `natural_rate_hypothesis_long_run_phillips_vertical` | 1.166 | 1 (`chicago_monetarism`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 21 | `labour_market_reform_almp_complementarity_effect` | 1.166 | 1 (`empirical_pragmatist`) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 22 | `automatic_stabiliser_2008_contraction_severity` | 1.166 | 1 (`social_democratic`) | `regulatory.trade_openness` | needs_successful_rerun |
| 23 | `universal_healthcare_cost_outcome_oecd` | 1.166 | 1 (`social_democratic`) | `fiscal.transfer_expansion` | needs_successful_rerun |
| 24 | `universal_vs_meanstest_child_poverty` | 1.166 | 1 (`social_democratic`) | `fiscal.transfer_expansion` | needs_successful_rerun |
| 25 | `cuba_special_period_degrowth_basic_needs` | 1.159 | 1 (`degrowth`) | `fiscal.transfer_expansion` | needs_successful_rerun |
| 26 | `child_benefit_expansion_child_poverty_effect` | 1.159 | 1 (`democratic_socialist`) | `fiscal.transfer_expansion` | needs_successful_rerun |
| 27 | `corbyn_manifesto_capital_flight_prediction` | 1.159 | 1 (`democratic_socialist`) | `institutional.property_rights` | needs_successful_rerun |
| 28 | `federal_minimum_wage_employment_meta` | 1.159 | 1 (`democratic_socialist`) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 29 | `free_community_college_enrolment_completion` | 1.159 | 1 (`democratic_socialist`) | `fiscal.tax_progressivity` | needs_successful_rerun |
| 30 | `minimum_wage_employment_effect_us_states` | 1.159 | 1 (`democratic_socialist`) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 31 | `nova_industria_brasil_export_discipline_pattern_effect` | 1.159 | 1 (`developmentalism`) | `regulatory.trade_openness` | needs_run_dir |
| 32 | `singapore_cpf_national_savings_effect` | 1.159 | 1 (`developmentalism`) | `regulatory.trade_openness` | needs_successful_rerun |
| 33 | `eu_green_deal_vs_ets_emissions_mechanism` | 1.159 | 1 (`eco_socialist`) | `fiscal.sectoral_subsidy` | needs_successful_rerun |
| 34 | `uk_electricity_privatisation_price_decarbonisation` | 1.159 | 1 (`eco_socialist`) | `institutional.property_rights` | needs_successful_rerun |
| 35 | `voluntary_carbon_markets_real_abatement` | 1.159 | 1 (`eco_socialist`) | `regulatory.environmental_stringency` | needs_successful_rerun |
| 36 | `argentina_institutional_instability_decline` | 1.159 | 1 (`institutionalism`) | `institutional.rule_of_law` | needs_successful_rerun |
| 37 | `chile_post_1990_institutional_premium` | 1.159 | 1 (`institutionalism`) | `institutional.rule_of_law` | needs_successful_rerun |
| 38 | `colonial_institutions_post_independence_growth` | 1.159 | 1 (`institutionalism`) | `institutional.rule_of_law` | needs_successful_rerun |
| 39 | `singapore_cpf_institutional_complementarity` | 1.159 | 1 (`institutionalism`) | `institutional.rule_of_law` | needs_successful_rerun |
| 40 | `zimbabwe_property_rights_output_link` | 1.159 | 1 (`institutionalism`) | `institutional.property_rights` | needs_run_dir |
| 41 | `emilia_romagna_coop_employment_resilience` | 1.159 | 1 (`market_socialist`) | `regulatory.labour_market_flexibility` | needs_successful_rerun |
| 42 | `mondragon_cooperative_resilience` | 1.159 | 1 (`market_socialist`) | `institutional.property_rights` | needs_successful_rerun |
| 43 | `great_depression_over_accumulation_vs_monetary_cause` | 1.159 | 1 (`marxian`) | `regulatory.financial_deregulation` | needs_successful_rerun |
| 44 | `industrial_concentration_labour_share_link` | 1.159 | 1 (`marxian`) | `regulatory.trade_openness` | needs_successful_rerun |
| 45 | `productivity_compensation_decoupling_post_1973` | 1.159 | 1 (`marxian`) | `institutional.rule_of_law` | needs_successful_rerun |
| 46 | `milei_shock_therapy_poverty_and_real_wage_effect` | 1.159 | 1 (`marxist_leninist`) | `fiscal.spending_level` | needs_successful_rerun |
| 47 | `price_controls_produce_shortages_and_quality_degradation` | 1.159 | 1 (`marxist_leninist`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 48 | `soviet_collectivisation_agricultural_marketings` | 1.159 | 1 (`marxist_leninist`) | `institutional.property_rights` | needs_successful_rerun |
| 49 | `zimbabwe_land_reform_cause_decomposition` | 1.159 | 1 (`marxist_leninist`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 50 | `fiscal_multipliers_zlb_higher_than_normal_regime` | 1.159 | 1 (`new_keynesian`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 51 | `tcja_2017_growth_effect` | 1.159 | 1 (`new_keynesian`) | `fiscal.tax_corporate` | needs_successful_rerun |
| 52 | `abenomics_monetary_policy_demand_effect` | 1.159 | 1 (`post_keynesian`) | `monetary.monetary_expansion_direction` | needs_successful_rerun |
| 53 | `trump_tariff_manufacturing_reshoring_effect` | 1.159 | 1 (`post_keynesian`) | `regulatory.trade_openness` | needs_successful_rerun |
| 54 | `bismarckian_welfare_fiscal_sustainability` | 1.090 | 1 (`ordoliberal`) | `fiscal.transfer_expansion` | needs_successful_rerun |
| 55 | `competition_enforcement_consumer_welfare_effect` | 1.090 | 1 (`ordoliberal`) | `regulatory.product_market_competition` | needs_successful_rerun |

## First Batch IDs

Use the companion `.ids` file for automation input. The first 20 IDs are:
- `intergenerational_mobility_cross_country`
- `minimum_wage_above_median_employment_teen_effects`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `financial_liberalisation_crisis_risk`
- `industrial_policy_high_governance_success`
- `asia_taiwan_tsmc_industrial_policy_1985_2024`
- `china_renewables_industrial_policy_learning_curve`
- `natural_monopoly_private_failure`
- `fossil_subsidy_persistence_private_ownership_link`
- `macron_labour_tax_employment_distribution`
- `austerity_output_recovery_tradeoff`
- `welfare_architecture_market_openness_nordic`
- `rent_control_reduces_housing_supply_and_quality`
- `industrial_policy_semiconductor_chips_act_effectiveness`
- `frontier_tfp_market_liberal_panel_1970_2024`
- `fiat_expansion_erodes_currency_purchasing_power_long_run`
- `friedman_schwartz_great_depression_monetary_cause`
- `natural_rate_hypothesis_long_run_phillips_vertical`
