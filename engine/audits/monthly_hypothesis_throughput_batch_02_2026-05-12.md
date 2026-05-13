# Monthly Hypothesis Throughput Batch 02

Date: 2026-05-12

Purpose: continue the monthly hypothesis throughput plan in 30-run batches, prioritising already promoted hypotheses with runnable replication wrappers.

## Summary

- Runs attempted: 30
- Verdict-bearing results: 24
- Supported: 12
- Partial: 3
- Refuted: 9
- Inconclusive data/model-pending: 6

## Results

| Hypothesis | Result |
| --- | --- |
| `business_dynamism_frontier_income_growth` | refuted |
| `price_signal_integrity_qol_panel` | refuted |
| `platform_competition_dissipates_monopoly_rent` | refuted |
| `intervention_reversal_qol_loss_1980_2024` | supported |
| `latam_resource_nationalisation_social_outcome_tradeoff` | partial |
| `price_controls_food_output_decline_panel` | refuted |
| `caribbean_climate_resilience_panel_1990_2024` | inconclusive data/model-pending |
| `gfc_household_debt_wage_stagnation_link` | partial |
| `market_reform_female_education` | supported |
| `asia_bangladesh_apparel_growth_1985_2024` | inconclusive data/model-pending |
| `spectrum_auction_vs_administrative_allocation_telecom` | supported |
| `sea_singapore_fta_cascade_post_2014` | refuted |
| `banking_crisis_schularick_taylor_credit_boom_panel_post1980` | supported |
| `japan_miti_success_then_stagnation_panel` | inconclusive data/model-pending |
| `china_soe_vs_cee_privatised_growth` | inconclusive data/model-pending |
| `generic_substitution_mandate_savings_no_harm` | supported |
| `demo_canada_points_system_immigration` | inconclusive data/model-pending |
| `sea_indonesia_jokowi_infrastructure_2014_2024` | refuted |
| `bank_state_ownership_credit_misallocation` | refuted |
| `strong_union_labour_law_youth_unemployment_south_europe` | refuted |
| `market_income_school_completion` | supported |
| `india_extra_modi_era_growth_2014_2024` | supported |
| `demo_life_expectancy_lfp_panel` | inconclusive data/model-pending |
| `tax_simplicity_disposable_income_growth` | supported |
| `crony_capitalism_not_market_freedom` | supported |
| `market_institution_duration_qol_persistence` | refuted |
| `qol_anomaly_weight_broad_scope_test` | supported |
| `occupational_licensing_income_mobility` | supported |
| `demo_marriage_age_fertility_growth` | partial |
| `firm_entry_rate_long_run_productivity` | supported |

## Repair Queue

These are not failed verdicts. They need a different design or a better treatment series because the current fixed-effects setup absorbs the treatment.

- `caribbean_climate_resilience_panel_1990_2024`: treatment has no cross-country variation within years under year fixed effects.
- `asia_bangladesh_apparel_growth_1985_2024`: treatment has no within-country variation under country fixed effects.
- `japan_miti_success_then_stagnation_panel`: treatment has no within-country variation under country fixed effects.
- `china_soe_vs_cee_privatised_growth`: treatment has no within-country variation under country fixed effects.
- `demo_canada_points_system_immigration`: treatment has no within-country variation under country fixed effects.
- `demo_life_expectancy_lfp_panel`: treatment has no within-country variation under country fixed effects.

## QA Notes

- Several quality-of-life style runs share the same large coefficient shape. Before scoreboard conversion, inspect whether those hypotheses are intentionally reusing the same broad-scope panel or whether they need more specific treatments/outcomes.
- Refuted results should not be discarded. They are useful for keeping the framework honest and identifying where broad market claims need narrower conditions.
