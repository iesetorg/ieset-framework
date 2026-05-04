# School Tested Equalization Plan

Generated: 2026-05-04
Target tested prediction rows per school: `122`

## Methodology Gate

- Unit is scoreboard prediction rows, not net scores and not unique hypothesis IDs.
- Existing hidden linked claims are repaired before any new links are recommended.
- The plan does not change verdicts, polarity, school predictions, or score weights.

## Summary

- Schools tracked: 17
- Current tested range: 123-146
- Total tested gap to target: 0
- Gap fillable by repairing existing hidden linked claims: 0
- New link/new hypothesis gap after repairs: 0
- Blocker counts: `{'needs_successful_rerun': 149, 'needs_run_dir': 2}`

## School Gaps

| school | tested | untested | hidden linked | unlinked | gap | repair existing | new link gap | top blockers | top axes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `post_keynesian` | 123 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | fiscal.tax_progressivity (2), fiscal.spending_level (1), monetary.monetary_expansion_direction (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `new_keynesian` | 123 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.tax_corporate (2), fiscal.tax_progressivity (2), monetary.monetary_expansion_direction (1), fiscal.spending_level (1), fiscal.tax_capital (1) |
| `institutionalism` | 123 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (9), needs_run_dir (1) | institutional.rule_of_law (4), institutional.property_rights (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `developmentalism` | 123 | 7 | 7 | 0 | 0 | 0 | 0 | needs_successful_rerun (6), needs_run_dir (1) | regulatory.trade_openness (2), fiscal.sectoral_subsidy (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `chicago_monetarism` | 123 | 7 | 7 | 0 | 0 | 0 | 0 | needs_successful_rerun (7) | monetary.monetary_expansion_direction (2), regulatory.product_market_competition (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `social_democratic` | 124 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.transfer_expansion (2), fiscal.spending_level (1), fiscal.tax_corporate (1), regulatory.trade_openness (1), fiscal.tax_capital (1) |
| `mmt` | 124 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.tax_capital (1), regulatory.energy_supply_security (1), regulatory.labour_market_flexibility (1) |
| `marxist_leninist` | 124 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | monetary.monetary_expansion_direction (2), fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), institutional.property_rights (1), fiscal.spending_level (1) |
| `marxian` | 124 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.tax_progressivity (2), fiscal.sectoral_subsidy (2), regulatory.financial_deregulation (1), institutional.rule_of_law (1), regulatory.trade_openness (1) |
| `market_socialist` | 124 | 10 | 10 | 0 | 0 | 0 | 0 | needs_successful_rerun (10) | fiscal.sectoral_subsidy (3), regulatory.labour_market_flexibility (2), fiscal.tax_progressivity (2), institutional.property_rights (1), fiscal.tax_capital (1) |
| `empirical_pragmatist` | 124 | 7 | 7 | 0 | 0 | 0 | 0 | needs_successful_rerun (7) | regulatory.labour_market_flexibility (2), fiscal.sectoral_subsidy (1), fiscal.tax_corporate (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `eco_socialist` | 124 | 11 | 11 | 0 | 0 | 0 | 0 | needs_successful_rerun (11) | fiscal.sectoral_subsidy (4), fiscal.tax_progressivity (2), institutional.property_rights (1), regulatory.environmental_stringency (1), fiscal.tax_capital (1) |
| `democratic_socialist` | 124 | 13 | 13 | 0 | 0 | 0 | 0 | needs_successful_rerun (13) | regulatory.labour_market_flexibility (3), fiscal.tax_progressivity (3), fiscal.sectoral_subsidy (2), regulatory.product_market_competition (1), institutional.property_rights (1) |
| `degrowth` | 124 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | fiscal.sectoral_subsidy (3), fiscal.tax_progressivity (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |
| `austrian` | 125 | 5 | 5 | 0 | 0 | 0 | 0 | needs_successful_rerun (5) | monetary.monetary_expansion_direction (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1), regulatory.labour_market_flexibility (1) |
| `ordoliberal` | 134 | 8 | 8 | 0 | 0 | 0 | 0 | needs_successful_rerun (8) | regulatory.product_market_competition (2), fiscal.transfer_expansion (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1), fiscal.tax_progressivity (1) |
| `classical_liberal` | 146 | 9 | 9 | 0 | 0 | 0 | 0 | needs_successful_rerun (9) | regulatory.product_market_competition (2), regulatory.labour_market_flexibility (2), regulatory.trade_openness (1), fiscal.tax_capital (1), regulatory.energy_supply_security (1) |

## First Repair Queue

| school | claim | hypothesis | reason | axis | runner |
| --- | ---: | --- | --- | --- | --- |
| `post_keynesian` | 13 | `trump_tariff_manufacturing_reshoring_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 5 | `singapore_cpf_national_savings_effect` | `needs_successful_rerun` | `regulatory.trade_openness` | `-` |
| `marxian` | 10 | `industrial_concentration_labour_share_link` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 7 | `china_1978_price_liberalisation_growth_decomposition` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_event_study.py` |
| `social_democratic` | 13 | `automatic_stabiliser_2008_contraction_severity` | `needs_successful_rerun` | `regulatory.trade_openness` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 12 | `restrictive_zoning_housing_supply_elasticity` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `chicago_monetarism` | 11 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `classical_liberal` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `democratic_socialist` | 1 | `rent_control_reduces_housing_supply_and_quality` | `needs_successful_rerun` | `regulatory.product_market_competition` | `-` |
| `ordoliberal` | 3 | `competition_enforcement_consumer_welfare_effect` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `ordoliberal` | 12 | `competition_enforcement_consumer_welfare_effect` | `needs_successful_rerun` | `regulatory.product_market_competition` | `scripts/run_panel_fe.py` |
| `classical_liberal` | 11 | `occupational_licensing_productivity_drag` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_panel_fe.py` |
| `democratic_socialist` | 4 | `minimum_wage_employment_effect_us_states` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `austrian` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `chicago_monetarism` | 65 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `classical_liberal` | 64 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `degrowth` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `democratic_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `developmentalism` | 66 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |
| `eco_socialist` | 63 | `minimum_wage_above_median_employment_teen_effects` | `needs_successful_rerun` | `regulatory.labour_market_flexibility` | `scripts/run_did_callaway_santanna.py` |

## First Repair IDs

Use this list for bounded rerun/repair waves; repeated IDs can affect multiple schools.
- `trump_tariff_manufacturing_reshoring_effect`
- `singapore_cpf_national_savings_effect`
- `industrial_concentration_labour_share_link`
- `china_1978_price_liberalisation_growth_decomposition`
- `automatic_stabiliser_2008_contraction_severity`
- `restrictive_zoning_housing_supply_elasticity`
- `rent_control_reduces_housing_supply_and_quality`
- `competition_enforcement_consumer_welfare_effect`
- `occupational_licensing_productivity_drag`
- `minimum_wage_employment_effect_us_states`
- `minimum_wage_above_median_employment_teen_effects`
- `labour_market_reform_almp_complementarity_effect`
- `federal_minimum_wage_employment_meta`
- `emilia_romagna_coop_employment_resilience`
- `great_depression_over_accumulation_vs_monetary_cause`
- `voluntary_carbon_markets_real_abatement`
- `nuclear_phaseout_grid_reliability_cost_tradeoff`
- `zimbabwe_land_reform_cause_decomposition`
- `price_controls_produce_shortages_and_quality_degradation`
- `natural_rate_hypothesis_long_run_phillips_vertical`
