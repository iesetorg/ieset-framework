# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `120`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 105-145
- Total tested gap to target: 138
- Gap fillable by repairing existing hidden linked claims: 138
- New link/new hypothesis gap after repairs: 0
- Blocker counts: `{'needs_successful_rerun': 176, 'needs_run_dir': 2}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `democratic_socialist` | 105 | 15 | 15 | 0 | 15 | 15 | 0 | needs_successful_rerun (15) | regulatory.labour_market_flexibility (3), fiscal.tax_progressivity (3), institutional.property_rights (2), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1) |
| `marxist_leninist` | 107 | 13 | 13 | 0 | 13 | 13 | 0 | needs_successful_rerun (13) | monetary.monetary_expansion_direction (2), institutional.property_rights (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), fiscal.spending_level (1) |
| `eco_socialist` | 107 | 13 | 13 | 0 | 13 | 13 | 0 | needs_successful_rerun (13) | fiscal.sectoral_subsidy (4), institutional.property_rights (2), fiscal.tax_progressivity (2), regulatory.environmental_stringency (1), fiscal.tax_capital (1) |
| `marxian` | 108 | 12 | 12 | 0 | 12 | 12 | 0 | needs_successful_rerun (12) | regulatory.financial_deregulation (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), institutional.rule_of_law (1), regulatory.trade_openness (1) |
| `market_socialist` | 108 | 12 | 12 | 0 | 12 | 12 | 0 | needs_successful_rerun (12) | fiscal.sectoral_subsidy (3), institutional.property_rights (2), regulatory.labour_market_flexibility (2), fiscal.tax_progressivity (2), fiscal.tax_capital (1) |
| `institutionalism` | 109 | 11 | 11 | 0 | 11 | 11 | 0 | needs_successful_rerun (10), needs_run_dir (1) | institutional.rule_of_law (4), institutional.property_rights (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `degrowth` | 109 | 11 | 11 | 0 | 11 | 11 | 0 | needs_successful_rerun (11) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `social_democratic` | 110 | 11 | 11 | 0 | 10 | 10 | 0 | needs_successful_rerun (11) | fiscal.transfer_expansion (2), regulatory.trade_openness (2), regulatory.labour_market_flexibility (2), fiscal.spending_level (1), fiscal.tax_corporate (1) |
| `new_keynesian` | 110 | 10 | 10 | 0 | 10 | 10 | 0 | needs_successful_rerun (10) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `mmt` | 110 | 10 | 10 | 0 | 10 | 10 | 0 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), regulatory.labour_market_flexibility (1) |
| `post_keynesian` | 111 | 9 | 9 | 0 | 9 | 9 | 0 | needs_successful_rerun (9) | fiscal.tax_progressivity (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `chicago_monetarism` | 113 | 8 | 8 | 0 | 7 | 7 | 0 | needs_successful_rerun (8) | monetary.monetary_expansion_direction (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `developmentalism` | 117 | 8 | 8 | 0 | 3 | 3 | 0 | needs_successful_rerun (7), needs_run_dir (1) | regulatory.trade_openness (3), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `empirical_pragmatist` | 118 | 9 | 9 | 0 | 2 | 2 | 0 | needs_successful_rerun (9) | regulatory.labour_market_flexibility (3), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `austrian` | 124 | 6 | 6 | 0 | 0 | 0 | 0 | needs_successful_rerun (6) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 132 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `classical_liberal` | 145 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | regulatory.product_market_competition (2), regulatory.trade_openness (2), regulatory.labour_market_flexibility (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `democratic_socialist` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `democratic_socialist` | 4 | `minimum_wage_employment_effect_us_states` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 12 | `federal_minimum_wage_employment_meta` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 93 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `democratic_socialist` | 97 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `democratic_socialist` | 10 | `corbyn_manifesto_capital_flight_prediction` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `democratic_socialist` | 13 | `child_benefit_expansion_child_poverty_effect` | `needs_successful_rerun` | `fiscal.transfer_expansion` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 81 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `democratic_socialist` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `democratic_socialist` | 7 | `free_community_college_enrolment_completion` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 21 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `democratic_socialist` | 99 | `china_renewables_industrial_policy_learning_curve` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `democratic_socialist` | 98 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `eco_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxist_leninist` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 90 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `marxist_leninist` | 93 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `eco_socialist` | 9 | `voluntary_carbon_markets_real_abatement` | `needs_successful_rerun` | `regulatory.environmental_stringency` | `scripts/run_descriptive.py` |
| `eco_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxist_leninist` | 25 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxist_leninist` | 7 | `zimbabwe_land_reform_cause_decomposition` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `marxist_leninist` | 1 | `price_controls_produce_shortages_and_quality_degradation` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_synth_did.py` |
| `eco_socialist` | 6 | `uk_electricity_privatisation_price_decarbonisation` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `marxist_leninist` | 10 | `soviet_collectivisation_agricultural_marketings` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_descriptive.py` |
| `eco_socialist` | 94 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `marxist_leninist` | 97 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `eco_socialist` | 77 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `marxist_leninist` | 80 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `eco_socialist` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `marxist_leninist` | 27 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `eco_socialist` | 21 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `marxist_leninist` | 20 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `marxist_leninist` | 12 | `milei_shock_therapy_poverty_and_real_wage_effect` | `needs_successful_rerun` | `fiscal.spending_level` | `scripts/run_event_study.py` |
| `eco_socialist` | 3 | `fossil_subsidy_persistence_private_ownership_link` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `eco_socialist` | 12 | `eu_green_deal_vs_ets_emissions_mechanism` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_event_study.py` |
| `eco_socialist` | 8 | `china_renewables_industrial_policy_learning_curve` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `marxist_leninist` | 99 | `china_renewables_industrial_policy_learning_curve` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `eco_socialist` | 95 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `marxist_leninist` | 98 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `marxian` | 10 | `industrial_concentration_labour_share_link` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `market_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 7 | `emilia_romagna_coop_employment_resilience` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_synth_did.py` |
| `marxian` | 4 | `great_depression_over_accumulation_vs_monetary_cause` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_descriptive.py` |
| `market_socialist` | 88 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `marxian` | 90 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `market_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxian` | 7 | `productivity_compensation_decoupling_post_1973` | `needs_successful_rerun` | `institutional.rule_of_law` | `-` |
| `market_socialist` | 92 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `marxian` | 94 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `market_socialist` | 3 | `mondragon_cooperative_resilience` | `needs_successful_rerun` | `institutional.property_rights` | `-` |
| `market_socialist` | 76 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `marxian` | 78 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `market_socialist` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `marxian` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `market_socialist` | 21 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `marxian` | 23 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `market_socialist` | 98 | `fossil_subsidy_persistence_private_ownership_link` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `market_socialist` | 94 | `china_renewables_industrial_policy_learning_curve` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `marxian` | 96 | `china_renewables_industrial_policy_learning_curve` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `scripts/run_descriptive.py` |
| `market_socialist` | 93 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `marxian` | 95 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `institutionalism` | 72 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `degrowth` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `institutionalism` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 89 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `degrowth` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `institutionalism` | 27 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `institutionalism` | 5 | `singapore_cpf_institutional_complementarity` | `needs_successful_rerun` | `institutional.rule_of_law` | `scripts/run_synth_did.py` |
| `institutionalism` | 2 | `colonial_institutions_post_independence_growth` | `needs_successful_rerun` | `institutional.rule_of_law` | `scripts/run_panel_fe.py` |
| `institutionalism` | 7 | `chile_post_1990_institutional_premium` | `needs_successful_rerun` | `institutional.rule_of_law` | `-` |
| `institutionalism` | 13 | `argentina_institutional_instability_decline` | `needs_successful_rerun` | `institutional.rule_of_law` | `-` |
| `degrowth` | 93 | `natural_monopoly_private_failure` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_event_study.py` |
| `institutionalism` | 69 | `frontier_tfp_market_liberal_panel_1970_2024` | `needs_successful_rerun` | `institutional.property_rights` | `scripts/run_panel_fe.py` |
| `degrowth` | 5 | `cuba_special_period_degrowth_basic_needs` | `needs_successful_rerun` | `fiscal.transfer_expansion` | `-` |
| `degrowth` | 76 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `degrowth` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `rent_control_reduces_housing_supply_and_quality`
- `minimum_wage_employment_effect_us_states`
- `minimum_wage_above_median_employment_teen_effects`
- `federal_minimum_wage_employment_meta`
- `financial_liberalisation_crisis_risk`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `natural_monopoly_private_failure`
- `corbyn_manifesto_capital_flight_prediction`
- `child_benefit_expansion_child_poverty_effect`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `intergenerational_mobility_cross_country`
- `free_community_college_enrolment_completion`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `china_renewables_industrial_policy_learning_curve`
- `asia_taiwan_tsmc_industrial_policy_1985_2024`
- `voluntary_carbon_markets_real_abatement`
- `zimbabwe_land_reform_cause_decomposition`
- `price_controls_produce_shortages_and_quality_degradation`
- `uk_electricity_privatisation_price_decarbonisation`
- `soviet_collectivisation_agricultural_marketings`
- `milei_shock_therapy_poverty_and_real_wage_effect`
- `fossil_subsidy_persistence_private_ownership_link`
- `eu_green_deal_vs_ets_emissions_mechanism`
- `industrial_concentration_labour_share_link`
- `emilia_romagna_coop_employment_resilience`
- `great_depression_over_accumulation_vs_monetary_cause`
- `productivity_compensation_decoupling_post_1973`
- `mondragon_cooperative_resilience`
- `industrial_policy_high_governance_success`
- `singapore_cpf_institutional_complementarity`
- `colonial_institutions_post_independence_growth`
- `chile_post_1990_institutional_premium`
- `argentina_institutional_instability_decline`
- `frontier_tfp_market_liberal_panel_1970_2024`
- `cuba_special_period_degrowth_basic_needs`
- `zimbabwe_property_rights_output_link`
- `automatic_stabiliser_2008_contraction_severity`
- `welfare_architecture_market_openness_nordic`
- `fiscal_multipliers_zlb_higher_than_normal_regime`
- `universal_vs_meanstest_child_poverty`
- `universal_healthcare_cost_outcome_oecd`
- `tcja_2017_growth_effect`
- `macron_labour_tax_employment_distribution`
- `austerity_output_recovery_tradeoff`
- `trump_tariff_manufacturing_reshoring_effect`
- `abenomics_monetary_policy_demand_effect`
- `natural_rate_hypothesis_long_run_phillips_vertical`
- `friedman_schwartz_great_depression_monetary_cause`
- `singapore_cpf_national_savings_effect`
- `industrial_policy_semiconductor_chips_act_effectiveness`
- `nova_industria_brasil_export_discipline_pattern_effect`
- `labour_market_reform_almp_complementarity_effect`
- `china_1978_price_liberalisation_growth_decomposition`
- `restrictive_zoning_housing_supply_elasticity`
- `competition_enforcement_consumer_welfare_effect`
- `occupational_licensing_productivity_drag`
- `fiat_expansion_erodes_currency_purchasing_power_long_run`
- `bismarckian_welfare_fiscal_sustainability`
