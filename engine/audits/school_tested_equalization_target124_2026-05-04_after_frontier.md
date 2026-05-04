# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `124`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 123-147
- Total tested gap to target: 4
- Gap fillable by repairing existing hidden linked claims: 4
- New link/new hypothesis gap after repairs: 0
- Blocker counts: `{'needs_successful_rerun': 146, 'needs_run_dir': 2}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `post_keynesian` | 123 | 8 | 8 | 0 | 1 | 1 | 0 | needs_successful_rerun (8) | fiscal.tax_progressivity (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `new_keynesian` | 123 | 9 | 9 | 0 | 1 | 1 | 0 | needs_successful_rerun (9) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `developmentalism` | 123 | 7 | 7 | 0 | 1 | 1 | 0 | needs_successful_rerun (6), needs_run_dir (1) | regulatory.trade_openness (2), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `chicago_monetarism` | 123 | 7 | 7 | 0 | 1 | 1 | 0 | needs_successful_rerun (7) | monetary.monetary_expansion_direction (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `social_democratic` | 124 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.transfer_expansion (2), fiscal.spending_level (1), fiscal.tax_corporate (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `mmt` | 124 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), regulatory.labour_market_flexibility (1) |
| `marxist_leninist` | 124 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | monetary.monetary_expansion_direction (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), institutional.property_rights (1), fiscal.spending_level (1) |
| `marxian` | 124 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), regulatory.financial_deregulation (1), institutional.rule_of_law (1), regulatory.trade_openness (1) |
| `market_socialist` | 124 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), regulatory.labour_market_flexibility (2), fiscal.tax_progressivity (2), institutional.property_rights (1), fiscal.tax_capital (1) |
| `institutionalism` | 124 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (8), needs_run_dir (1) | institutional.rule_of_law (4), institutional.property_rights (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `empirical_pragmatist` | 124 | 7 | 7 | 0 | 0 | 0 | 0 | needs_successful_rerun (7) | regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `eco_socialist` | 124 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | fiscal.sectoral_subsidy (4), fiscal.tax_progressivity (2), institutional.property_rights (1), regulatory.environmental_stringency (1), fiscal.tax_capital (1) |
| `democratic_socialist` | 124 | 13 | 13 | 0 | 0 | 0 | 0 | needs_successful_rerun (13) | regulatory.labour_market_flexibility (3), fiscal.tax_progressivity (3), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1), institutional.property_rights (1) |
| `degrowth` | 124 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `austrian` | 125 | 5 | 5 | 0 | 0 | 0 | 0 | needs_successful_rerun (5) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 135 | 7 | 7 | 0 | 0 | 0 | 0 | needs_successful_rerun (7) | regulatory.product_market_competition (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `classical_liberal` | 147 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), regulatory.trade_openness (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `post_keynesian` | 13 | `trump_tariff_manufacturing_reshoring_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 5 | `singapore_cpf_national_savings_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `chicago_monetarism` | 11 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `chicago_monetarism` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `new_keynesian` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `post_keynesian` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `developmentalism` | 29 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `new_keynesian` | 26 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `post_keynesian` | 28 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | `needs_successful_rerun` | `regulatory.energy_supply_security` | `-` |
| `chicago_monetarism` | 4 | `natural_rate_hypothesis_long_run_phillips_vertical` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 5 | `friedman_schwartz_great_depression_monetary_cause` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_descriptive.py` |
| `new_keynesian` | 3 | `fiscal_multipliers_zlb_higher_than_normal_regime` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `-` |
| `post_keynesian` | 8 | `abenomics_monetary_policy_demand_effect` | `needs_successful_rerun` | `monetary.monetary_expansion_direction` | `scripts/run_event_study.py` |
| `new_keynesian` | 97 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `post_keynesian` | 83 | `tax_inequality_korea_progressive_turn_2017_2020` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `scripts/run_synth_did.py` |
| `chicago_monetarism` | 30 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `developmentalism` | 31 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |
| `new_keynesian` | 28 | `intergenerational_mobility_cross_country` | `needs_successful_rerun` | `fiscal.tax_progressivity` | `-` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `trump_tariff_manufacturing_reshoring_effect`
- `singapore_cpf_national_savings_effect`
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
- `nova_industria_brasil_export_discipline_pattern_effect`
- `industrial_concentration_labour_share_link`
- `china_1978_price_liberalisation_growth_decomposition`
- `automatic_stabiliser_2008_contraction_severity`
