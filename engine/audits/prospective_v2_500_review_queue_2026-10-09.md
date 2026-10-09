# Prospective v2 review queue for 500 legacy hypotheses

This is a prioritized audit queue, not 500 preregistrations or graduations. Every selected case already has an old run whose result may have been seen. The old same-commit history cannot be repaired by rerunning that ID.

This design-review queue does not track subsequent v2 results. For live graduation totals, use the refreshed evidence-tier audit and hypothesis conversion funnel.

- Legacy pool: **1,320**
- Selected for design review: **500**
- Registrations or graduations created by this queue script: **0**

## Selected old-spec status

| Status | Cases |
| --- | ---: |
| `candidate` | 306 |
| `draft` | 50 |
| `pre_registered` | 144 |

## Review flags

| Flag | Cases |
| --- | ---: |
| `estimator_floor_failure` | 1 |
| `few_panel_units_review` | 2 |
| `heritage_cross_section_direct_measure_review` | 104 |
| `missing_variables` | 10 |
| `old_evidence_packet_missing` | 335 |
| `old_manifest_missing` | 124 |
| `old_result_not_canonical` | 11 |
| `old_spec_requires_full_design_review` | 356 |
| `screening_or_proxy_design` | 147 |

## First 40 review cases

| Rank | Hypothesis | Topic | Old result | Next action |
| ---: | --- | --- | --- | --- |
| 1 | `biden_ira_chips_fiscal_inflation_pass_through` | labour | supported | review old test and specify independent holdout or new design |
| 2 | `canada_gdp_per_capita_stagnation_post_2015` | growth | supported | review old test and specify independent holdout or new design |
| 3 | `top_1_percent_income_share_growth_drivers` | distribution | supported | review old test and specify independent holdout or new design |
| 4 | `albania_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 5 | `argentina_cepo_lift_2015_fx_inflation_reserves` | monetary | supported | review old test and specify independent holdout or new design |
| 6 | `armenia_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 7 | `asian_convergence_vs_western_stagnation_2000_2023` | growth | supported | review old test and specify independent holdout or new design |
| 8 | `bangladesh_growth_health_services_shift_1990_2023` | labour | supported | review old test and specify independent holdout or new design |
| 9 | `banking_crisis_brazil_proer_1995_1997` | regulatory | supported | review old test and specify independent holdout or new design |
| 10 | `banking_crisis_mexico_tequila_1994_canonical` | regulatory | refuted | review old test and specify independent holdout or new design |
| 11 | `banking_crisis_south_africa_african_bank_2014` | regulatory | supported | review old test and specify independent holdout or new design |
| 12 | `banking_crisis_turkey_2001_canonical` | regulatory | supported | review old test and specify independent holdout or new design |
| 13 | `banking_crisis_vietnam_2012_2015_restructuring` | regulatory | supported | review old test and specify independent holdout or new design |
| 14 | `bhutan_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 15 | `cambodia_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 16 | `chile_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 17 | `chile_vs_venezuela_divergence_1999_2023` | growth | supported | review old test and specify independent holdout or new design |
| 18 | `china_deng_reform_growth_acceleration_1978` | growth | supported | review old test and specify independent holdout or new design |
| 19 | `china_growth_health_services_shift_1990_2023` | growth | supported | review old test and specify independent holdout or new design |
| 20 | `eu_chemical_reach_regulation_firm_exit_effect` | regulatory | supported | review old test and specify independent holdout or new design |
| 21 | `fiat_expansion_erodes_currency_purchasing_power_long_run` | monetary | supported | review old test and specify independent holdout or new design |
| 22 | `fiscal_rule_presence_dampens_statist_drift` | institutional_quality | partial | review old test and specify independent holdout or new design |
| 23 | `german_manufacturing_va_decline_2017_2024` | growth | refuted | review old test and specify independent holdout or new design |
| 24 | `hong_kong_minimal_state_growth_miracle_1960_1997` | growth | supported | review old test and specify independent holdout or new design |
| 25 | `india_1991_liberalisation_growth_acceleration` | growth | supported | review old test and specify independent holdout or new design |
| 26 | `industrial_policy_developmentalist_states_growth` | growth | supported | review old test and specify independent holdout or new design |
| 27 | `initial_state_share_predicts_drift_reversal` | institutional_quality | partial | review old test and specify independent holdout or new design |
| 28 | `labour_market_flexibility_unemployment_duration` | labour | refuted | review old test and specify independent holdout or new design |
| 29 | `liberal_democracy_managerial_flywheel_drift` | institutional_quality | refuted | review old test and specify independent holdout or new design |
| 30 | `nordic_outcome_persistence_decomposition_v2` | institutional_quality | partial | review old test and specify independent holdout or new design |
| 31 | `oecd_collective_bargaining_growth_penalty_kei` | labour | supported | review old test and specify independent holdout or new design |
| 32 | `oecd_collective_bargaining_unemployment_nonpenalty` | labour | partial | review old test and specify independent holdout or new design |
| 33 | `oecd_union_density_disposable_gini_panel` | distribution | partial | review old test and specify independent holdout or new design |
| 34 | `post_soviet_market_reform_life_expectancy` | institutional_quality | refuted | review old test and specify independent holdout or new design |
| 35 | `singapore_lky_changi_air_hub_tourism_1981_2019` | trade | supported | review old test and specify independent holdout or new design |
| 36 | `singapore_lky_fdi_manufacturing_upgrade_1970_1990` | growth | supported | review old test and specify independent holdout or new design |
| 37 | `singapore_lky_financial_deepening_market_hub_1970_2020` | growth | supported | review old test and specify independent holdout or new design |
| 38 | `singapore_lky_growth_takeoff_1965_1990` | growth | supported | review old test and specify independent holdout or new design |
| 39 | `singapore_lky_high_tech_export_digital_upgrade_1990_2024` | growth | supported | review old test and specify independent holdout or new design |
| 40 | `singapore_lky_human_capital_upgrade_1965_2010` | labour | supported | review old test and specify independent holdout or new design |

All 500 selected cases and the 820 remaining legacy cases are in the JSON artifact; the selected 500 also have a compact CSV.

## Required sequence

1. Audit the old claim, outcome, sources, method, and any integrity finding.
2. Write a materially specified follow-up with a new hypothesis ID and steelman; disclose that the old result was seen.
3. Define an independent holdout, new data vintage, or genuinely revised estimand and fixed falsification rule.
4. Commit the new spec in git; only then estimate and commit run artifacts in a later commit.
5. Validate registration history, data provenance, replication, estimator floor, correction state, and second-order measurement.
6. Run evidence-tier and claim-level audits before any public/scoreboard credit.

Review priority is based on old artifact completeness and recorded method risks. It is not a probability of replication and never uses the old coefficient direction, p-value, or any expected school-score change.
