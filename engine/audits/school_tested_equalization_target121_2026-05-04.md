# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `121`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 121-145
- Total tested gap to target: 0
- Gap fillable by repairing existing hidden linked claims: 0
- New link/new hypothesis gap after repairs: 0
- Blocker counts: `{'needs_successful_rerun': 176, 'needs_run_dir': 2}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `social_democratic` | 121 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | fiscal.transfer_expansion (2), regulatory.trade_openness (2), regulatory.labour_market_flexibility (2), fiscal.spending_level (1), fiscal.tax_corporate (1) |
| `post_keynesian` | 121 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.tax_progressivity (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `new_keynesian` | 121 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `mmt` | 121 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), regulatory.labour_market_flexibility (1) |
| `marxist_leninist` | 121 | 13 | 13 | 0 | 0 | 0 | 0 | needs_successful_rerun (13) | monetary.monetary_expansion_direction (2), institutional.property_rights (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), fiscal.spending_level (1) |
| `marxian` | 121 | 12 | 12 | 0 | 0 | 0 | 0 | needs_successful_rerun (12) | regulatory.financial_deregulation (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), institutional.rule_of_law (1), regulatory.trade_openness (1) |
| `market_socialist` | 121 | 12 | 12 | 0 | 0 | 0 | 0 | needs_successful_rerun (12) | fiscal.sectoral_subsidy (3), institutional.property_rights (2), regulatory.labour_market_flexibility (2), fiscal.tax_progressivity (2), fiscal.tax_capital (1) |
| `institutionalism` | 121 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (10), needs_run_dir (1) | institutional.rule_of_law (4), institutional.property_rights (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `empirical_pragmatist` | 121 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | regulatory.labour_market_flexibility (3), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `eco_socialist` | 121 | 13 | 13 | 0 | 0 | 0 | 0 | needs_successful_rerun (13) | fiscal.sectoral_subsidy (4), institutional.property_rights (2), fiscal.tax_progressivity (2), regulatory.environmental_stringency (1), fiscal.tax_capital (1) |
| `developmentalism` | 121 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (7), needs_run_dir (1) | regulatory.trade_openness (3), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `democratic_socialist` | 121 | 15 | 15 | 0 | 0 | 0 | 0 | needs_successful_rerun (15) | regulatory.labour_market_flexibility (3), fiscal.tax_progressivity (3), institutional.property_rights (2), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1) |
| `degrowth` | 121 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `chicago_monetarism` | 121 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | monetary.monetary_expansion_direction (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `austrian` | 124 | 6 | 6 | 0 | 0 | 0 | 0 | needs_successful_rerun (6) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 132 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `classical_liberal` | 145 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | regulatory.product_market_competition (2), regulatory.trade_openness (2), regulatory.labour_market_flexibility (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `post_keynesian` | 13 | `trump_tariff_manufacturing_reshoring_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 5 | `singapore_cpf_national_savings_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `austrian` | 68 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 69 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 78 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `developmentalism` | 104 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `empirical_pragmatist` | 74 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `institutionalism` | 72 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `new_keynesian` | 76 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `ordoliberal` | 66 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `social_democratic` | 75 | `industrial_policy_high_governance_success` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `marxian` | 10 | `industrial_concentration_labour_share_link` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 7 | `china_1978_price_liberalisation_growth_decomposition` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_event_study.py` |
| `social_democratic` | 13 | `automatic_stabiliser_2008_contraction_severity` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 12 | `restrictive_zoning_housing_supply_elasticity` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 11 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `classical_liberal` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `democratic_socialist` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `ordoliberal` | 3 | `competition_enforcement_consumer_welfare_effect` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `ordoliberal` | 12 | `competition_enforcement_consumer_welfare_effect` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `empirical_pragmatist` | 97 | `welfare_architecture_market_openness_nordic` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `ordoliberal` | 88 | `welfare_architecture_market_openness_nordic` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `social_democratic` | 97 | `welfare_architecture_market_openness_nordic` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 11 | `occupational_licensing_productivity_drag` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 4 | `minimum_wage_employment_effect_us_states` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `austrian` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `classical_liberal` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `empirical_pragmatist` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `institutionalism` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxist_leninist` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `mmt` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `new_keynesian` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `ordoliberal` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `social_democratic` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `empirical_pragmatist` | 10 | `labour_market_reform_almp_complementarity_effect` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 12 | `federal_minimum_wage_employment_meta` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 7 | `emilia_romagna_coop_employment_resilience` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_synth_did.py` |
| `marxian` | 4 | `great_depression_over_accumulation_vs_monetary_cause` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_descriptive.py` |
| `degrowth` | 89 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 93 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `eco_socialist` | 90 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `market_socialist` | 88 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `marxian` | 90 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `marxist_leninist` | 93 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `mmt` | 88 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `post_keynesian` | 96 | `financial_liberalisation_crisis_risk` | `needs_successful_rerun` | `regulatory.financial_deregulation` | `scripts/run_panel_fe.py` |
| `eco_socialist` | 9 | `voluntary_carbon_markets_real_abatement` | `needs_successful_rerun` | `regulatory.environmental_stringency` | `scripts/run_descriptive.py` |
| `austrian` | 29 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `chicago_monetarism` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `classical_liberal` | 27 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `degrowth` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `democratic_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `developmentalism` | 29 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `eco_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `empirical_pragmatist` | 27 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `institutionalism` | 27 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `market_socialist` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxist_leninist` | 25 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `mmt` | 25 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `new_keynesian` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `ordoliberal` | 25 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `post_keynesian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `social_democratic` | 27 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `marxist_leninist` | 7 | `zimbabwe_land_reform_cause_decomposition` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `marxist_leninist` | 1 | `price_controls_produce_shortages_and_quality_degradation` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_synth_did.py` |
| `chicago_monetarism` | 4 | `natural_rate_hypothesis_long_run_phillips_vertical` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 5 | `friedman_schwartz_great_depression_monetary_cause` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_descriptive.py` |
| `new_keynesian` | 3 | `fiscal_multipliers_zlb_higher_than_normal_regime` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `-` |
| `austrian` | 2 | `fiat_expansion_erodes_currency_purchasing_power_long_run` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `post_keynesian` | 8 | `abenomics_monetary_policy_demand_effect` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_event_study.py` |
| `institutionalism` | 5 | `singapore_cpf_institutional_complementarity` | `needs_successful_rerun` | `institutional.rule_of_law` | `scripts/run_synth_did.py` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `trump_tariff_manufacturing_reshoring_effect`
- `singapore_cpf_national_savings_effect`
- `industrial_policy_high_governance_success`
- `industrial_concentration_labour_share_link`
- `china_1978_price_liberalisation_growth_decomposition`
- `automatic_stabiliser_2008_contraction_severity`
- `restrictive_zoning_housing_supply_elasticity`
- `rent_control_reduces_housing_supply_and_quality`
- `competition_enforcement_consumer_welfare_effect`
- `welfare_architecture_market_openness_nordic`
- `occupational_licensing_productivity_drag`
- `minimum_wage_employment_effect_us_states`
- `minimum_wage_above_median_employment_teen_effects`
- `labour_market_reform_almp_complementarity_effect`
- `federal_minimum_wage_employment_meta`
- `emilia_romagna_coop_employment_resilience`
- `great_depression_over_accumulation_vs_monetary_cause`
- `financial_liberalisation_crisis_risk`
- `voluntary_carbon_markets_real_abatement`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `zimbabwe_land_reform_cause_decomposition`
- `price_controls_produce_shortages_and_quality_degradation`
- `natural_rate_hypothesis_long_run_phillips_vertical`
- `friedman_schwartz_great_depression_monetary_cause`
- `fiscal_multipliers_zlb_higher_than_normal_regime`
- `fiat_expansion_erodes_currency_purchasing_power_long_run`
- `abenomics_monetary_policy_demand_effect`
- `singapore_cpf_institutional_complementarity`
- `productivity_compensation_decoupling_post_1973`
- `colonial_institutions_post_independence_growth`
- `chile_post_1990_institutional_premium`
- `argentina_institutional_instability_decline`
- `uk_electricity_privatisation_price_decarbonisation`
- `soviet_collectivisation_agricultural_marketings`
- `natural_monopoly_private_failure`
- `mondragon_cooperative_resilience`
- `frontier_tfp_market_liberal_panel_1970_2024`
- `corbyn_manifesto_capital_flight_prediction`
- `universal_vs_meanstest_child_poverty`
- `universal_healthcare_cost_outcome_oecd`
- `cuba_special_period_degrowth_basic_needs`
- `child_benefit_expansion_child_poverty_effect`
- `bismarckian_welfare_fiscal_sustainability`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `intergenerational_mobility_cross_country`
- `free_community_college_enrolment_completion`
- `tcja_2017_growth_effect`
- `macron_labour_tax_employment_distribution`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `milei_shock_therapy_poverty_and_real_wage_effect`
- `austerity_output_recovery_tradeoff`
- `industrial_policy_semiconductor_chips_act_effectiveness`
- `fossil_subsidy_persistence_private_ownership_link`
- `eu_green_deal_vs_ets_emissions_mechanism`
- `china_renewables_industrial_policy_learning_curve`
- `asia_taiwan_tsmc_industrial_policy_1985_2024`
- `nova_industria_brasil_export_discipline_pattern_effect`
- `zimbabwe_property_rights_output_link`
