# Remaining Stash Cleanup Audit

Generated: 2026-05-14

## Scope

This audit reviews the preserved stash `audit-cleanup-pre-reconcile-20260513` after the decisive and partial cleanup waves were committed to `origin/main`.

It is intentionally conservative: remaining artifacts should not be bulk-applied to the live tree. The prior two waves already extracted the clean result-bearing work.

## Current conclusion

- Ready-to-graduate result runs remaining: 0
- Data-pending/inconclusive runs remaining: 10
- Malformed or missing-verdict diagnostics remaining: 2
- Low-identification decisive-looking runs deferred: 3
- Suspicious generic-zero partial runs deferred: 6
- Thin partial run deferred: 1

## Deferred data-pending runs

These are useful work items, but they need data or estimator repair before graduation:

- `abenomics_monetary_fiscal_coordination_effect` - cannot infer event year.
- `caribbean_climate_resilience_panel_1990_2024` - treatment has no cross-country variation with year fixed effects.
- `child_benefit_expansion_child_poverty_effect` - insufficient post-deletion observations.
- `dialysis_market_competition_outcome_quality` - treatment has no within-country variation under country fixed effects.
- `federal_minimum_wage_employment_meta` - missing BLS low-wage outcome data.
- `industrial_concentration_labour_share_link` - missing concentration/treatment data.
- `ira_2022_clean_energy_investment_decomposition` - missing decomposition channel.
- `japan_miti_success_then_stagnation_panel` - treatment has no within-country variation.
- `nuclear_phaseout_grid_reliability_cost_tradeoff` - missing primary outcome data.
- `privatisation_transition_tfp_panel` - treatment has no within-country variation.

## Malformed diagnostics

These should be repaired or rerun before any scoreboard use:

- `albania_growth_health_services_shift_1990_2023`
- `armenia_growth_health_services_shift_1990_2023`

## Low-identification decisive-looking runs

These carry decisive labels in the stash but are not rigorous enough to graduate:

- `abct_credit_boom_predicts_capital_misallocation_oecd` - supported label, but only 2 countries, 59 observations, and pathological p-value/R2 behavior.
- `hayek_regulatory_uncertainty_investment_chilling` - refuted label, but only 2 countries and 46 observations.
- `strong_union_labour_law_youth_unemployment_south_europe` - refuted label, but only 5 countries and weak diagnostics.

## Suspicious generic-zero partials

These broad panels all show effectively-zero coefficients from the same runner pattern and should be QAed before graduation:

- `CBDC_design_privacy_tradeoff`
- `active_labour_market_policy_conditionality_works`
- `agricultural_export_ban_price_instability`
- `agricultural_trade_liberalisation_food_security`
- `apprenticeship_employer_chamber_quality`
- `liberal_capital_account_openness_growth_premium_panel`

## Thin partial

- `us_eu_gdp_per_capita_divergence_policy_causes` - partial, but only 30 observations. Keep as candidate only if strengthened with a better long-panel or richer comparator design.

## Stale or separate work

- Stashed scoreboard audit files after `wave24b`, `wave25c`, and related temporary visibility reports are stale relative to the current `origin/main` audit chain.
- Stashed web edits are stale relative to the already-pushed full hypothesis search UI.
- `Reply Guy/` is a separate side project and should be handled on its own branch, not mixed into IESET hypothesis graduation.
- Untracked daily BLS backfill artifacts from 2026-05-13 landed zero rows because DNS/network access failed. They should not be committed as data progress; rerun the backfill with working network/API settings instead.

## Next best work

The next real throughput lever is not another stash extraction. It is targeted repair of the data-pending group:

1. Fix BLS access for `federal_minimum_wage_employment_meta`.
2. Replace no-variation treatments with event-study or cross-sectional designs for Japan MITI, Caribbean CCRIF, dialysis competition, and privatisation.
3. Add missing primary data for nuclear reliability/cost outcomes.
4. Rebuild concentration treatment data for `industrial_concentration_labour_share_link`.
5. Rerun and only graduate outputs with adequate sample size, non-pathological diagnostics, and clear falsification mapping.
