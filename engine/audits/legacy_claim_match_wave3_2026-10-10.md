# Legacy claim-match wave 3: no new conversion

Date: 2026-10-10. Base: `840a07dba46c680b656aa264f9cc113edb5ec2cc` on an isolated managed worktree.
This is a source-key, specification, and overlap review of selected leads in the
1,320 legacy same-commit queue. It did not read selected outcome magnitudes,
outcome null masks, fit a model, change any old record, or confer public credit.
The status of the unreviewed remainder of the queue is not inferred from these
selected cases.

## Decision

**Do not register a nominal new-ID test from this screened subset.** The
readily measurable continuations already have separate v2 records. The
remaining attractive claims here need a missing direct construct, an actual
new time window, or a claim-specific comparator design. A different geography
with a weaker proxy would neither repair the archived run nor add an
independent test of its original claim.

| Legacy claim | Current opportunity | Decision |
| --- | --- | --- |
| `cross_school_private_credit_manufacturing_financialisation_1990_2023` | A 2022-to-2024 manufacturing-share continuation exists as `private_credit_manufacturing_share_2022_2024_holdout_v2`. | Duplicate measured question; no second credit/manufacturing conversion from the same WDI vintage. |
| `cross_school_trade_openness_growth_1990_2023` | `trade_openness_gdp_pc_growth_geographic_holdout_v2` already asks the direct country-disjoint growth question. | Duplicate. |
| `economic_freedom_index_income_correlation`, `financial_market_depth_productivity`, `female_lfp_market_opportunity` | The three designs in `legacy_wdi_wgi_owid_panel_v2_coverage_review_2026-10-09.md` are now recorded as `fraser_freedom_forward_income_geographic_holdout_v2`, `private_credit_tfp_growth_geographic_holdout_v2`, and `services_share_female_lfp_geographic_holdout_v2`. | All three opportunities already exercised; their limitations and registered family rule carry through. |
| `working_time_reduction_employment_neutral_oecd` | `working_time_employment_oecd_geographic_holdout_v2` already uses the unused OECD countries and a genuine equivalence interval. | Duplicate; do not infer a French hours-policy effect from the descriptive hours/employment panel. |
| `union_density_inequality_growth_oecd` | `oecd_union_density_disposable_gini_panel` already joins OECD union density to disposable-income Gini across the OECD. | The inequality half is already measured. A further country slice would not test the old no-growth-cost conjunction; it needs an equivalence margin and a distinct growth outcome. |
| `demo_higher_ed_expansion_growth` | Local WDI tertiary-attainment keys and PWT TFP keys exist. PWT `rtfpna` vintage stops in 2019, while the archived claim names Korea, Taiwan, and Ireland, a high-tech-export channel, and a comparator-based growth contrast. Two existing tertiary-attainment tests already use growth/output-per-worker endpoints. | A country-disjoint tertiary-to-TFP correlation would omit the named-country and high-tech components. No post-old-period PWT TFP window is locally pinned. Do not count a narrowed correlation as this claim's rescue. |
| `austrian_savings_rate_investment_quality_link` | WDI gross savings and formation, PWT TFP, and a BIS credit-gap series exist. | Gross savings and a credit gap are not the registered decomposition of **savings-financed versus credit-financed investment** or the 1.5 elasticity ratio. PWT TFP again ends in 2019, inside the old specified period. A separate savings/TFP correlation is not full claim-matched evidence. |
| `australia_super_guarantee_saving_effect` | Local WDI national savings rows exist. | The specified primary household saving rate, pension-asset stock, APRA/RBA series, and voluntary-saving offset are absent from the local vintage inventory. National savings cannot establish no crowd-out. |
| `canada_real_disposable_income_post_2015` | Old local WDI GDP/GNP substitutes exist. | No exact OECD household disposable-income `DSD_NASEC_T14` local vintage was found; GDP/GNP is not the claimed household outcome. |

## Evidence boundary and next acquisition

The earlier `legacy_archive_v2_readiness_2026-10-10.md` found only 22 of
203 fully source-pinned legacy pairs with any confirmed added raw calendar
year; those additions cluster in a BIS property quarter, OECD labour force
2025, one ECB rate observation, and a few OECD housing-inequality cells. An
added year is not by itself a claim-matched independent holdout. The same
archive audit identifies tax-revenue/child-mortality as a two-year modeled
outcome lead, too short to establish the claimed public-capacity mechanism.

The most useful acquisitions for this screened subset are: official household
saving and pension-asset vintages for Australian superannuation, the OECD
household disposable-income series for the Canada claim, and a documented
investment-financing decomposition for the Austrian savings claim. Before any
new test, fix its direct outcome, source and release pins, non-overlap,
comparison set, estimator, sample and concentration floors, and family error
rule in a committed registration. Then source-lock, run, and exact-replay in
separate later commits. Keep legacy same-commit results archived; give no
school, policy, causal, featured, or public-count credit to this audit.

Read-only checks: existing hypothesis paths; `rg --files --no-ignore` inventory
of the main checkout's ignored vintages; Parquet schemas and country/year keys
only for the WDI tertiary and PWT TFP files. The dirty main checkout was not
modified. The isolated checkout itself contains fewer raw vintages than main,
so absence here was cross-checked against main before recording a data gap.
