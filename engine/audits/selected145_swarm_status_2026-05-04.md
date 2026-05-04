# Selected 145 Swarm Status

Generated: 2026-05-04

## Methodology Gate

- Existing linked pending hypotheses are exhausted before adding new hypotheses or new school links.
- Reruns are allowed to graduate only when the preregistered data/spec gate is actually satisfied.
- Inconclusive reruns remain blockers; they are not treated as school wins or losses.

## Swarm Assignments

- `minimum_wage`: minimum_wage_above_median_employment_teen_effects; minimum_wage_employment_effect_us_states
- `intergenerational_mobility`: intergenerational_mobility_cross_country
- `nuclear_grid`: nuclear_phaseout_grid_reliability_cost_tradeoff
- `wealth_tax_fra`: wealth_tax_capital_flight_revenue_yield_gap
- `laeven_valencia`: financial_liberalisation_crisis_risk
- `irena_iea_energy`: china_renewables_industrial_policy_learning_curve; fossil_subsidy_persistence_private_ownership_link

## Current Selected 145 Queue Summary

- Under-covered schools: 16
- Pending candidates with coverage benefit: 55
- Linked gap remaining after pending runs: 195
- Tested gap after exhausting pending runs: 195
- Reason counts: `{'needs_run_dir': 2, 'needs_successful_rerun': 53}`

## Attempted Existing Pending Runs

- Attempts: 32
- Unique attempted hypotheses: 32
- Outcome categories: `{'missing_treatment_data': 7, 'missing_outcome_data': 8, 'missing_decomposition_channel': 1, 'insufficient_coverage': 8, 'needs_sharpened_rule': 5, 'missing_country_panel': 1, 'missing_outcome_or_treatment': 1, 'other': 1}`

| rank | hypothesis | schools helped | runner | status | latest blocker |
| ---: | --- | ---: | --- | --- | --- |
| 1 | `intergenerational_mobility_cross_country` | 16 | `-` | `not_attempted` | not_attempted |
| 2 | `minimum_wage_above_median_employment_teen_effects` | 16 | `scripts/run_did_callaway_santanna.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| 3 | `nuclear_phaseout_grid_reliability_cost_tradeoff` | 16 | `-` | `not_attempted` | not_attempted |
| 4 | `wealth_tax_capital_flight_revenue_yield_gap` | 16 | `scripts/run_synth_did.py` | `missing_country_panel` | INCONCLUSIVE_DATA_PENDING — FRA not in panel |
| 5 | `tax_inequality_korea_progressive_turn_2017_2020` | 9 | `scripts/run_synth_did.py` | `insufficient_coverage` | INCONCLUSIVE_DATA_PENDING — insufficient pre-period coverage (years=10, donors=1) |
| 6 | `financial_liberalisation_crisis_risk` | 8 | `scripts/run_panel_fe.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['constructed:laeven_valencia_crisis_database', 'constructed:laeven_valencia_crisis_database', 'constructed:peak_to |
| 7 | `industrial_policy_high_governance_success` | 8 | `scripts/run_panel_fe.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['oecd_stan:manufacturing_tfp; constructed:unido_indstat', 'constructed:hauskornrich_export_sophistication; world_b |
| 8 | `asia_taiwan_tsmc_industrial_policy_1985_2024` | 7 | `-` | `not_attempted` | not_attempted |
| 9 | `china_renewables_industrial_policy_learning_curve` | 7 | `scripts/run_descriptive.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['irena:solar_pv_costs', 'irena:wind_lcoe'] |
| 10 | `natural_monopoly_private_failure` | 7 | `scripts/run_event_study.py` | `missing_treatment_data` | INCONCLUSIVE_DATA_PENDING — no treatment variable resolved |
| 11 | `fossil_subsidy_persistence_private_ownership_link` | 4 | `scripts/run_descriptive.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['iea:fossil_fuel_subsidies; imf:imf_energy_subsidies', 'iea:fossil_fuel_subsidies'] |
| 12 | `macron_labour_tax_employment_distribution` | 3 | `scripts/run_event_study.py` | `insufficient_coverage` | INCONCLUSIVE_DATA_PENDING — insufficient pre/post obs (pre=3, post=6) |
| 13 | `austerity_output_recovery_tradeoff` | 3 | `-` | `not_attempted` | not_attempted |
| 14 | `welfare_architecture_market_openness_nordic` | 3 | `scripts/run_panel_fe.py` | `missing_decomposition_channel` | INCONCLUSIVE_DATA_PENDING — no decomposition channel loaded; missing: [] |
| 15 | `rent_control_reduces_housing_supply_and_quality` | 2 | `-` | `not_attempted` | not_attempted |
| 16 | `industrial_policy_semiconductor_chips_act_effectiveness` | 2 | `-` | `not_attempted` | not_attempted |
| 17 | `frontier_tfp_market_liberal_panel_1970_2024` | 2 | `scripts/run_panel_fe.py` | `missing_treatment_data` | INCONCLUSIVE_DATA_PENDING — no treatment variable loaded; missing: ['fraser_efw:regulation_property_rights_trade; oecd:product_market_regulation', 'oecd:state_control_pmr; vdem:sta |
| 18 | `fiat_expansion_erodes_currency_purchasing_power_long_run` | 1 | `scripts/run_panel_fe.py` | `missing_outcome_or_treatment` | INCONCLUSIVE_DATA_PENDING — no outcome or no treatment variable in spec |
| 19 | `friedman_schwartz_great_depression_monetary_cause` | 1 | `scripts/run_descriptive.py` | `needs_sharpened_rule` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule with  |
| 20 | `natural_rate_hypothesis_long_run_phillips_vertical` | 1 | `scripts/run_panel_fe.py` | `needs_sharpened_rule` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule with  |
| 21 | `labour_market_reform_almp_complementarity_effect` | 1 | `scripts/run_panel_fe.py` | `missing_treatment_data` | INCONCLUSIVE_DATA_PENDING — no treatment variable loaded; missing: ['oecd:OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0', 'oecd:LMP_SPEND', 'constructed: (1 - EPL_OV) * almp_spending_share |
| 22 | `automatic_stabiliser_2008_contraction_severity` | 1 | `scripts/run_panel_fe.py` | `missing_treatment_data` | INCONCLUSIVE_DATA_PENDING — no treatment variable loaded; missing: ['oecd:SOCX_AGG', 'oecd:STWS'] |
| 23 | `universal_healthcare_cost_outcome_oecd` | 1 | `scripts/run_panel_fe.py` | `needs_sharpened_rule` | INCONCLUSIVE_DATA_PENDING — falsification rule not sharpened — auto-grader refuses to grade against the generic stub boilerplate. Promote the spec (replace falsification.rule with  |
| 24 | `universal_vs_meanstest_child_poverty` | 1 | `scripts/run_panel_fe.py` | `other` | INCONCLUSIVE_DATA_PENDING — interaction term requested but no loadable constructed interaction variable is defined. The generic panel_fe runner would otherwise grade a main-effect  |
| 25 | `cuba_special_period_degrowth_basic_needs` | 1 | `-` | `not_attempted` | not_attempted |
| 26 | `child_benefit_expansion_child_poverty_effect` | 1 | `scripts/run_did_callaway_santanna.py` | `insufficient_coverage` | INCONCLUSIVE_DATA_PENDING — insufficient obs after listwise deletion (2) |
| 27 | `corbyn_manifesto_capital_flight_prediction` | 1 | `scripts/run_event_study.py` | `insufficient_coverage` | INCONCLUSIVE_DATA_PENDING — insufficient pre/post obs (pre=2, post=4) |
| 28 | `federal_minimum_wage_employment_meta` | 1 | `scripts/run_did_callaway_santanna.py` | `missing_outcome_data` | INCONCLUSIVE_DATA_PENDING — no outcome variable loaded |
| 29 | `free_community_college_enrolment_completion` | 1 | `scripts/run_did_callaway_santanna.py` | `not_attempted` | not_attempted |
| 30 | `minimum_wage_employment_effect_us_states` | 1 | `scripts/run_did_callaway_santanna.py` | `missing_treatment_data` | INCONCLUSIVE_DATA_PENDING — no treatment variable loaded |

## Integration Priority

1. `intergenerational_mobility_cross_country` — helps 16 schools; latest: not_attempted
2. `minimum_wage_above_median_employment_teen_effects` — helps 16 schools; latest: INCONCLUSIVE_DATA_PENDING — no outcome variable loaded
3. `nuclear_phaseout_grid_reliability_cost_tradeoff` — helps 16 schools; latest: not_attempted
4. `wealth_tax_capital_flight_revenue_yield_gap` — helps 16 schools; latest: INCONCLUSIVE_DATA_PENDING — FRA not in panel
5. `financial_liberalisation_crisis_risk` — helps 8 schools; latest: INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['constructed:laeven_valencia_crisis_database', 'constructed:laeven_valencia_crisis_database', 
6. `china_renewables_industrial_policy_learning_curve` — helps 7 schools; latest: INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['irena:solar_pv_costs', 'irena:wind_lcoe']
7. `fossil_subsidy_persistence_private_ownership_link` — helps 4 schools; latest: INCONCLUSIVE_DATA_PENDING — no outcome variable loaded; missing: ['iea:fossil_fuel_subsidies; imf:imf_energy_subsidies', 'iea:fossil_fuel_subsidies']
