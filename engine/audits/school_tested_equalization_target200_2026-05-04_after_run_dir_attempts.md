# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `200`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 123-147
- Total tested gap to target: 1261
- Gap fillable by repairing existing hidden linked claims: 148
- New link/new hypothesis gap after repairs: 1113
- Blocker counts: `{'needs_successful_rerun': 148}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `post_keynesian` | 123 | 8 | 8 | 0 | 77 | 8 | 69 | needs_successful_rerun (8) | fiscal.tax_progressivity (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `new_keynesian` | 123 | 9 | 9 | 0 | 77 | 9 | 68 | needs_successful_rerun (9) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `developmentalism` | 123 | 7 | 7 | 0 | 77 | 7 | 70 | needs_successful_rerun (7) | regulatory.trade_openness (2), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `chicago_monetarism` | 123 | 7 | 7 | 0 | 77 | 7 | 70 | needs_successful_rerun (7) | monetary.monetary_expansion_direction (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `social_democratic` | 124 | 9 | 9 | 0 | 76 | 9 | 67 | needs_successful_rerun (9) | fiscal.transfer_expansion (2), fiscal.spending_level (1), fiscal.tax_corporate (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `mmt` | 124 | 8 | 8 | 0 | 76 | 8 | 68 | needs_successful_rerun (8) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), regulatory.labour_market_flexibility (1) |
| `marxist_leninist` | 124 | 11 | 11 | 0 | 76 | 11 | 65 | needs_successful_rerun (11) | monetary.monetary_expansion_direction (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), institutional.property_rights (1), fiscal.spending_level (1) |
| `marxian` | 124 | 10 | 10 | 0 | 76 | 10 | 66 | needs_successful_rerun (10) | fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), regulatory.financial_deregulation (1), institutional.rule_of_law (1), regulatory.trade_openness (1) |
| `market_socialist` | 124 | 10 | 10 | 0 | 76 | 10 | 66 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), regulatory.labour_market_flexibility (2), fiscal.tax_progressivity (2), institutional.property_rights (1), fiscal.tax_capital (1) |
| `institutionalism` | 124 | 9 | 9 | 0 | 76 | 9 | 67 | needs_successful_rerun (9) | institutional.rule_of_law (4), institutional.property_rights (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `empirical_pragmatist` | 124 | 7 | 7 | 0 | 76 | 7 | 69 | needs_successful_rerun (7) | regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `eco_socialist` | 124 | 11 | 11 | 0 | 76 | 11 | 65 | needs_successful_rerun (11) | fiscal.sectoral_subsidy (4), fiscal.tax_progressivity (2), institutional.property_rights (1), regulatory.environmental_stringency (1), fiscal.tax_capital (1) |
| `democratic_socialist` | 124 | 13 | 13 | 0 | 76 | 13 | 63 | needs_successful_rerun (13) | regulatory.labour_market_flexibility (3), fiscal.tax_progressivity (3), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1), institutional.property_rights (1) |
| `degrowth` | 124 | 9 | 9 | 0 | 76 | 9 | 67 | needs_successful_rerun (9) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `austrian` | 125 | 5 | 5 | 0 | 75 | 5 | 70 | needs_successful_rerun (5) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 135 | 7 | 7 | 0 | 65 | 7 | 58 | needs_successful_rerun (7) | regulatory.product_market_competition (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `classical_liberal` | 147 | 8 | 8 | 0 | 53 | 8 | 45 | needs_successful_rerun (8) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), regulatory.trade_openness (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `post_keynesian` | 13 | `trump_tariff_manufacturing_reshoring_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 5 | `singapore_cpf_national_savings_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `developmentalism` | 15 | `nova_industria_brasil_export_discipline_pattern_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `chicago_monetarism` | 11 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `chicago_monetarism` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `new_keynesian` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 29 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `scripts/run_did_callaway_santanna.py` |
| `new_keynesian` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 4 | `natural_rate_hypothesis_long_run_phillips_vertical` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 5 | `friedman_schwartz_great_depression_monetary_cause` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_descriptive.py` |
| `new_keynesian` | 3 | `fiscal_multipliers_zlb_higher_than_normal_regime` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `-` |
| `post_keynesian` | 8 | `abenomics_monetary_policy_demand_effect` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_event_study.py` |
| `new_keynesian` | 97 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `post_keynesian` | 83 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `chicago_monetarism` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_panel_fe.py` |
| `developmentalism` | 31 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_panel_fe.py` |
| `new_keynesian` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_panel_fe.py` |
| `post_keynesian` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_panel_fe.py` |
| `new_keynesian` | 8 | `tcja_2017_growth_effect` | `needs_successful_rerun` | `fiscal.tax_corporate` | `scripts/run_local_projections.py` |
| `new_keynesian` | 7 | `macron_labour_tax_employment_distribution` | `needs_successful_rerun` | `fiscal.tax_corporate` | `scripts/run_event_study.py` |
| `chicago_monetarism` | 23 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `developmentalism` | 24 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `new_keynesian` | 21 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `post_keynesian` | 23 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `new_keynesian` | 5 | `austerity_output_recovery_tradeoff` | `needs_successful_rerun` | `fiscal.spending_level` | `-` |
| `post_keynesian` | 5 | `austerity_output_recovery_tradeoff` | `needs_successful_rerun` | `fiscal.spending_level` | `-` |
| `developmentalism` | 8 | `industrial_policy_semiconductor_chips_act_effectiveness` | `needs_successful_rerun` | `fiscal.sectoral_subsidy` | `-` |
| `marxian` | 10 | `industrial_concentration_labour_share_link` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `social_democratic` | 13 | `automatic_stabiliser_2008_contraction_severity` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `democratic_socialist` | 4 | `minimum_wage_employment_effect_us_states` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `empirical_pragmatist` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `institutionalism` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `trump_tariff_manufacturing_reshoring_effect`
- `singapore_cpf_national_savings_effect`
- `nova_industria_brasil_export_discipline_pattern_effect`
- `rent_control_reduces_housing_supply_and_quality`
- `minimum_wage_above_median_employment_teen_effects`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `natural_rate_hypothesis_long_run_phillips_vertical`
- `friedman_schwartz_great_depression_monetary_cause`
- `fiscal_multipliers_zlb_higher_than_normal_regime`
- `abenomics_monetary_policy_demand_effect`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `intergenerational_mobility_cross_country`
- `tcja_2017_growth_effect`
- `macron_labour_tax_employment_distribution`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `austerity_output_recovery_tradeoff`
- `industrial_policy_semiconductor_chips_act_effectiveness`
- `industrial_concentration_labour_share_link`
- `automatic_stabiliser_2008_contraction_severity`
- `minimum_wage_employment_effect_us_states`
- `labour_market_reform_almp_complementarity_effect`
- `federal_minimum_wage_employment_meta`
- `emilia_romagna_coop_employment_resilience`
- `great_depression_over_accumulation_vs_monetary_cause`
- `voluntary_carbon_markets_real_abatement`
- `zimbabwe_land_reform_cause_decomposition`
- `price_controls_produce_shortages_and_quality_degradation`
- `singapore_cpf_institutional_complementarity`
- `productivity_compensation_decoupling_post_1973`
- `colonial_institutions_post_independence_growth`
- `chile_post_1990_institutional_premium`
- `argentina_institutional_instability_decline`
- `zimbabwe_property_rights_output_link`
- `uk_electricity_privatisation_price_decarbonisation`
- `soviet_collectivisation_agricultural_marketings`
- `mondragon_cooperative_resilience`
- `corbyn_manifesto_capital_flight_prediction`
- `universal_vs_meanstest_child_poverty`
- `universal_healthcare_cost_outcome_oecd`
- `cuba_special_period_degrowth_basic_needs`
