# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `200`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 122-147
- Total tested gap to target: 1270
- Gap fillable by repairing existing hidden linked claims: 157
- New link/new hypothesis gap after repairs: 1113
- Blocker counts: `{'needs_successful_rerun': 157}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `post_keynesian` | 122 | 9 | 9 | 0 | 78 | 9 | 69 | needs_successful_rerun (9) | fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1) |
| `chicago_monetarism` | 122 | 8 | 8 | 0 | 78 | 8 | 70 | needs_successful_rerun (8) | monetary.monetary_expansion_direction (2), regulatory.labour_market_flexibility (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `new_keynesian` | 123 | 9 | 9 | 0 | 77 | 9 | 68 | needs_successful_rerun (9) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `mmt` | 123 | 9 | 9 | 0 | 77 | 9 | 68 | needs_successful_rerun (9) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `marxist_leninist` | 123 | 12 | 12 | 0 | 77 | 12 | 65 | needs_successful_rerun (12) | monetary.monetary_expansion_direction (2), fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (2), institutional.property_rights (1) |
| `marxian` | 123 | 11 | 11 | 0 | 77 | 11 | 66 | needs_successful_rerun (11) | fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (2), regulatory.financial_deregulation (1), institutional.rule_of_law (1) |
| `market_socialist` | 123 | 11 | 11 | 0 | 77 | 11 | 66 | needs_successful_rerun (11) | regulatory.labour_market_flexibility (3), fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), institutional.property_rights (1), fiscal.tax_capital (1) |
| `eco_socialist` | 123 | 12 | 12 | 0 | 77 | 12 | 65 | needs_successful_rerun (12) | fiscal.sectoral_subsidy (4), fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), institutional.property_rights (1), regulatory.environmental_stringency (1) |
| `developmentalism` | 123 | 7 | 7 | 0 | 77 | 7 | 70 | needs_successful_rerun (7) | regulatory.trade_openness (2), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `democratic_socialist` | 123 | 14 | 14 | 0 | 77 | 14 | 63 | needs_successful_rerun (14) | regulatory.labour_market_flexibility (4), fiscal.tax_progressivity (3), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1), institutional.property_rights (1) |
| `degrowth` | 123 | 10 | 10 | 0 | 77 | 10 | 67 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), regulatory.labour_market_flexibility (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1) |
| `social_democratic` | 124 | 9 | 9 | 0 | 76 | 9 | 67 | needs_successful_rerun (9) | fiscal.transfer_expansion (2), fiscal.spending_level (1), fiscal.tax_corporate (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `institutionalism` | 124 | 9 | 9 | 0 | 76 | 9 | 67 | needs_successful_rerun (9) | institutional.rule_of_law (4), institutional.property_rights (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `empirical_pragmatist` | 124 | 7 | 7 | 0 | 76 | 7 | 69 | needs_successful_rerun (7) | regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `austrian` | 125 | 5 | 5 | 0 | 75 | 5 | 70 | needs_successful_rerun (5) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 135 | 7 | 7 | 0 | 65 | 7 | 58 | needs_successful_rerun (7) | regulatory.product_market_competition (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `classical_liberal` | 147 | 8 | 8 | 0 | 53 | 8 | 45 | needs_successful_rerun (8) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), regulatory.trade_openness (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `post_keynesian` | 13 | `trump_tariff_manufacturing_reshoring_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 11 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `chicago_monetarism` | 12 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 90 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `post_keynesian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `chicago_monetarism` | 4 | `natural_rate_hypothesis_long_run_phillips_vertical` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 5 | `friedman_schwartz_great_depression_monetary_cause` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_descriptive.py` |
| `post_keynesian` | 8 | `abenomics_monetary_policy_demand_effect` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_event_study.py` |
| `post_keynesian` | 83 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `chicago_monetarism` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `post_keynesian` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `chicago_monetarism` | 23 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `post_keynesian` | 23 | `wealth_tax_capital_flight_revenue_yield_gap` | `needs_successful_rerun` | `fiscal.tax_capital` | `scripts/run_synth_did.py` |
| `post_keynesian` | 5 | `austerity_output_recovery_tradeoff` | `needs_successful_rerun` | `fiscal.spending_level` | `-` |
| `developmentalism` | 5 | `singapore_cpf_national_savings_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `developmentalism` | 15 | `nova_industria_brasil_export_discipline_pattern_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `marxian` | 10 | `industrial_concentration_labour_share_link` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `democratic_socialist` | 4 | `minimum_wage_employment_effect_us_states` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 83 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 87 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 84 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 82 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxian` | 84 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxist_leninist` | 87 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `mmt` | 82 | `minimum_wage_disemployment_at_high_bite_ratios` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `marxist_leninist` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `mmt` | 62 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `new_keynesian` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 12 | `federal_minimum_wage_employment_meta` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `market_socialist` | 7 | `emilia_romagna_coop_employment_resilience` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_synth_did.py` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `trump_tariff_manufacturing_reshoring_effect`
- `rent_control_reduces_housing_supply_and_quality`
- `minimum_wage_disemployment_at_high_bite_ratios`
- `minimum_wage_above_median_employment_teen_effects`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `natural_rate_hypothesis_long_run_phillips_vertical`
- `friedman_schwartz_great_depression_monetary_cause`
- `abenomics_monetary_policy_demand_effect`
- `tax_inequality_korea_progressive_turn_2017_2020`
- `intergenerational_mobility_cross_country`
- `wealth_tax_capital_flight_revenue_yield_gap`
- `austerity_output_recovery_tradeoff`
- `singapore_cpf_national_savings_effect`
- `nova_industria_brasil_export_discipline_pattern_effect`
- `industrial_concentration_labour_share_link`
- `minimum_wage_employment_effect_us_states`
- `federal_minimum_wage_employment_meta`
- `emilia_romagna_coop_employment_resilience`
- `great_depression_over_accumulation_vs_monetary_cause`
- `voluntary_carbon_markets_real_abatement`
- `zimbabwe_land_reform_cause_decomposition`
- `price_controls_produce_shortages_and_quality_degradation`
- `fiscal_multipliers_zlb_higher_than_normal_regime`
- `productivity_compensation_decoupling_post_1973`
- `uk_electricity_privatisation_price_decarbonisation`
- `soviet_collectivisation_agricultural_marketings`
- `mondragon_cooperative_resilience`
- `corbyn_manifesto_capital_flight_prediction`
- `cuba_special_period_degrowth_basic_needs`
- `child_benefit_expansion_child_poverty_effect`
- `free_community_college_enrolment_completion`
- `tcja_2017_growth_effect`
- `macron_labour_tax_employment_distribution`
- `milei_shock_therapy_poverty_and_real_wage_effect`
- `industrial_policy_semiconductor_chips_act_effectiveness`
- `fossil_subsidy_persistence_private_ownership_link`
- `eu_green_deal_vs_ets_emissions_mechanism`
- `china_renewables_industrial_policy_learning_curve`
- `asia_taiwan_tsmc_industrial_policy_1985_2024`
- `automatic_stabiliser_2008_contraction_severity`
