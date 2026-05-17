# High-Quality Graduation Batch 2 — 2026-05-16

## Purpose

Run another careful graduation pass against hypotheses that were previously blocked by small source-resolution, local-vintage, or estimator-identification gaps. This batch prioritised verdict quality over count: source bridges had to point to real local vintages, panel slices had to be semantically narrow, and FE treatments had to be genuinely identified.

## Repairs Applied

- Materialised `pwt:rconna` from the local Penn World Table full file.
  - Vintage: `data/vintages/pwt/rconna@2026-05-16T114235Z.parquet`
  - Manifest: `data/manifests/fetch_run_2026-05-16T114237Z.yaml`
- Added source bridges in `scripts/run_panel_fe.py`:
  - `imf:WEO.NGDP_RPCH` -> `imf:NGDP_RPCH`
  - stale OECD SOCX aggregate URNs -> local `DSD_SOCX_DF_SOCX_AGG` vintage
  - `un_comtrade:export_product_concentration` -> `wits:export_product_hhi_wits`
- Added a narrow SOCX slice for `public_pension_expenditure_share_gdp`:
  - unit: percent of GDP
  - expenditure source: public
  - programme type: old age
- Fixed FRED single-country inference for Japan-coded series used by Japan/Abenomics specs (`JPNCPIALLMINMEI`, `DEXJPUS`, JGB yield series, etc.).
- Fixed constructed-treatment parsing so `from YEAR onward` is treated as an open-ended post period rather than a one-year pulse.
- Improved panel control pruning so optional controls can be dropped when they destroy FE treatment identification, not only when they reduce observation count.
- Corrected `demo_life_expectancy_lfp_panel` to use local WHO GHO `WHOSIS_000015` instead of the placeholder life-expectancy source.
- Added explicit `event_year: 2013` and a concrete falsification test to the Abenomics monetary-fiscal spec.
- Added pre-periods to the Australia Hawke-Keating and Bangladesh apparel specs so the post-treatment indicators are identified under country fixed effects.

## Primary Graduations

| Hypothesis | Verdict | Key estimate | Notes |
| --- | --- | --- | --- |
| `abenomics_monetary_fiscal_coordination_effect` | SUPPORTED | ITS mean post gap `+6.836`, `z=+17` | Now uses explicit 2013 event year; inflation expectations remain missing context, not a primary gate. |
| `asia_bangladesh_apparel_growth_1985_2024` | SUPPORTED | `coef=+1.201`, `p=0.00951`, `n=245`, `countries=5` | Pre-period added; SAARC panel now identifies BGD post-1985 treatment. |
| `quality_adjusted_consumption_market_liberal_panel` | PARTIAL | `coef=-0.03337`, `p=0.189`, `n=954`, `countries=37` | PWT `rconna` unlocked the real consumption outcome; variety proxy remains missing. |
| `demo_life_expectancy_lfp_panel` | PARTIAL | `coef=-0.4826`, `p=0.331`, `n=660`, `countries=30` | WHO life expectancy now loads with variation; pension-age control remains missing. |
| `demo_ageing_pension_burden_cross_country` | PARTIAL | `coef=+0.09129`, `p=0.172`, `n=695`, `countries=30` | SOCX old-age public pension spending slice now loads cleanly. |
| `australia_hawke_keating_reform_long_run` | PARTIAL | `coef=-0.01702`, `p=0.550`, `n=770`, `countries=14` | Pre-period and FE-identification pruning unlock a real DiD-style panel; controls dropped: human capital, commodity terms of trade, WGI government effectiveness. |

## Secondary Real Verdicts

These produced non-inconclusive artifacts, but should be treated as research-grade until the estimand is tightened.

| Hypothesis | Verdict | Why research-grade |
| --- | --- | --- |
| `tax_inequality_brazil_tax_base_evolution` | PARTIAL | Single-country time-series fallback runs, but claim direction was not auto-inferred. |
| `monopoly_capital_concentration_markup_link` | PARTIAL | Aggregate proxy run is usable, but the registered claim wants industry-level concentration/markup data. |
| `japan_sargent_wallace_refutation_1990_2024` | PARTIAL | FRED Japan mapping unlocked the outcome, but the generic descriptive threshold parser is not yet the right test for the debt/yield/inflation gate. Needs a bespoke Japan threshold evaluator before scoreboard use. |

## Honest Blockers Rechecked

- `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`: still `INCONCLUSIVE`, complete-case `n=13`; needs constructed CPI-divergence series or broader country-source coverage.
- `consumer_choice_variety_trade_market_reform`: still `INCONCLUSIVE`; PMR competition reform has no usable within-country variation and true import product-line variety is not loaded.
- `competition_enforcement_consumer_welfare_effect`: still `INCONCLUSIVE`, complete-case `n=22`; needs HHI and consumer price/marginal-cost series.
- `global_value_chain_participation_upgrade`: still `INCONCLUSIVE`, complete-case `n=23`; needs GVC participation/backward/forward linkage series.
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`: still `INCONCLUSIVE`, complete-case `n=21`; needs broader overlap or a bespoke lower-frequency design.
- `high_income_escape_market_openness_1950_2024`: still `INCONCLUSIVE`, complete-case `n=8`; needs tariff and human-capital coverage.
- `oecd_product_market_deregulation_tfp_panel`: still `INCONCLUSIVE`; PMR treatment has no within-country variation in the loaded slice.

## Next Best Targets

1. Build a bespoke Japan debt/yield/inflation descriptive evaluator and rerun both Japan solvency/Sargent-Wallace specs.
2. Create a derived CPI-divergence panel for the central-bank balance-sheet decoupling hypothesis.
3. Convert Bangladesh and Australia into result-strengthened wrappers that report the endpoint/sub-test metrics in the falsification text, not only the generic FE coefficient.
4. Add true import/export product-line variety vintages so consumer-choice and export-complexity specs do not have to proxy product variety through concentration.
