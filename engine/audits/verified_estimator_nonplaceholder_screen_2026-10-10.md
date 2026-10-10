# Verified estimator archive: 24-case source and method screen — 2026-10-10

Read-only audit of the clean consolidated checkpoint `cfbf2f6cb6970ffa1a184ccd45e7de1afc8de80c`. The current conversion funnel has 155 verified archived cases whose first action is `estimator_repair_and_rerun`. Exactly 131 saved runs combine WDI GDP per person as both outcome and control with the Fraser summary index as treatment; their near-zero coefficients are placeholders unrelated to the varied claims. This screen examines the other **24**. It changes no specification, result, verdict, tier, gate, or source vintage and claims **zero** conversions.

The 24 divide into **16 with declared inputs still missing in their saved runs** and **eight with no saved `variables_missing` flag but a failed or undefined primary/full-rule estimator**. An absent flag does not establish that all registered variables were correctly constructed. The first-registration comparison used `engine/preregistration_index.json` and the historical spec at its `spec_commit`; the run screen used `engine/runs/<id>/diagnostics.json`, the current spec, and prior case-specific reviews.

## Eight apparent data-ready cases: all remain archived

| ID | Decisive frozen-rule blocker |
| --- | --- |
| `canada_market_liberalisation_vs_state_industry_1988_2024` | Claim, sample, variables, estimator, and falsification changed after first registration. Saved FE fallback is rank deficient and near zero; it does not implement the registered Canada counterfactual. |
| `costa_rica_social_democratic_model_1980_2024` | Saved `SUPPORTED` is from a `context_inferred_treatment` FE fallback. The registered Costa Rica interaction and donor definition are not fixed precisely enough to select a unique frozen model; the HDI/ranking rule was not fully replayed. |
| `dominican_tourism_freezone_model_1980_2024` | Saved `REFUTED` is from a `context_inferred_treatment` fallback, not the full zone/tourism test. The locally reviewed Dominican 2019 tourism-receipts-share endpoint is null. |
| `paraguay_long_stable_growth_2003_2024` | Primary FE is rank deficient. The frozen rule does not define how to exclude 2020–21 from a 2003–24 cumulative endpoint, aggregate rolling volatility, or identify the Paraguay FE interaction. |
| `peru_post_fujimori_growth_2001_2019` | Independent method review rejects the post-result linear-trend choice as a frozen fit: “Peru-indicator interacted with year” and WGI/control roles do not select a unique model. The source-pinned draft is not a v1 repair. |
| `privatisation_transition_tfp_panel` | Exact preflight found zero countries with within-country mass-privatisation treatment changes after the registered WGI control starts; country FE absorbs the treatment. No primary estimate was fitted. |
| `uk_thatcher_market_reform_40yr_services_frontier` | Claim, sample, variables, estimator, and falsification changed after first registration. Saved FE fallback is rank deficient and effectively zero, not a full frozen 40-year services test. |
| `uruguay_frente_amplio_social_investment_2005_2020` | Primary FE is rank deficient and “URY-indicator interaction” is not specified sufficiently to choose a unique model. The four descriptive thresholds cannot substitute for the registered primary estimator. |

## Sixteen cases with missing declared inputs

| ID | Current source or full-test gap |
| --- | --- |
| `bankruptcy_law_efficiency_capital_reallocation` | Missing actual insolvency indicators, firm-capital reallocation, and bailout fiscal cost in the saved run. WGI rule-of-law proxy treatment was added after first registration and cannot repair v1. |
| `caribbean_climate_resilience_panel_1990_2024` | No source-custodied country-year storm-intensity index; CCRIF membership alone cannot answer the storm × insurance interaction or growth-gap decomposition. |
| `constitutional_fiscal_rules_growth_stability` | Long-run prosperity index missing; saved fallback also failed to fit the declared binding-rule variable and did not execute the three-condition rule. |
| `demo_japan_ageing_deflation_link` | Exact first-registration FRED `JPNM2MB` and IMF output-gap inputs absent; current spec changed output-gap source to OECD. Saved country FE regression is not the registered Johansen VECM plus comparator ranking. |
| `ecuador_correa_default_2008` | Debt, interest-payment and capital-formation outcomes plus declared risk controls were absent in the saved run. The claim's EMBI borrowing-cost and buyback-fiscal comparison are not measured by its generic GDP fallback. |
| `housing_supply_flexibility_real_wage` | Registered real-wage/rent construction, product-entry barrier, and household-debt inputs missing; a supply-elasticity proxy alone does not test the real-wage claim. |
| `japan_miti_success_then_stagnation_panel` | Manufacturing TFP, product-entry barriers, and zombie-firm channel missing; claim, sample, variables, estimator, and falsification also changed after first registration. |
| `judicial_independence_growth_persistence` | Actual V-Dem judicial composite and `v2x_jucon` not loaded in the saved run; the fallback on a generic reform episode is a different exposure. |
| `korea_post_chaebol_liberalisation_frontier_growth` | Top-five chaebol asset concentration missing; saved FE was rank deficient and did not execute the registered structural break. |
| `labour_flexibility_security_complement` | OECD EPL and union-density inputs missing; saved FE is rank deficient and its near-zero coefficient does not test the security interaction. |
| `mena_gcc_oil_price_decoupling_2014_2024` | Non-oil GDP growth, VAT introduction, and SWF assets missing; fiscal-balance source was changed after first registration. |
| `politicised_credit_election_cycle_growth_drag` | Declared development-bank credit, election timing, NPL, and terms-of-trade inputs missing; no primary event study was fitted. |
| `subsidy_duration_declining_returns_panel` | Sector value-added and subsidy-intensity series missing; a duration-only FE fallback does not test the quadratic dose/return claim. |
| `tax_simplicity_entrepreneurship_panel` | Firm-size employment, tax-rate, informality, and self-employment inputs missing; saved fallback does not meet the multi-outcome rule. |
| `welfare_state_market_flexibility_complement` | Household disposable-income and employment-channel inputs missing; sample and treatment source changed after first registration. The saved near-zero FE does not test the specified welfare × flexibility interaction. |
| `wto_accession_productivity_spillover_panel` | OECD PMR ETCR, WITS import penetration, and foreign tariff-access inputs missing. Saved TWFE fallback is not the registered staggered DiD with pre-trend, interaction, and ex-China checks. |

## Closest prospective v2 lead and why it is not ready

The dirty main checkout retains `data/vintages/doing_business/all_data@2026-05-02T201433Z.parquet`. Header rows identify separate insolvency time, recovery-rate, and framework-strength fields. Key/null-only inspection found all three fields for the original bankruptcy claim's 40 countries in 2004–2020 (680 country-years). A proposed *country holdout* outside those original 40 has 655 potential country-year keys across 70 countries in 2005–14 with pre-event Doing Business fields, WDI GDP-growth keys, and PWT TFP values at both five-year endpoints. These are upper bounds, not qualifying recessions or results; no PWT outcome magnitudes or model estimates were read.

This is **not yet a source-locked prospective design**. The local Doing Business file is a converted, wide parquet with no corresponding publisher raw file or fetch manifest in `data/`; its header explicitly marks methodology changes across DB10–14, DB15, and DB17–20. The declared Laeven–Valencia crisis vintage yields only one original-sample 2005–15 crisis onset with pre-shock insolvency fields and five-year TFP endpoints (`HUN`, 2008). The alternate JST/OWID crisis series yields 13 country events in 2007–08, overwhelmingly one shared global shock rather than 13 independent episodes. The first-registration v1 also aliases `IC.REC.COST` to both a cost-based index and a recovery-rate field, while the local Doing Business table distinguishes those measures. Selecting a new treatment, crisis definition, event clock, and sample now would be a **new-ID** design. The source custody, comparable indicator definition, event support, and a genuinely distinct held-out test must be frozen before outcome inspection.

## Ranked next actions

1. Acquire the original publisher Doing Business release, documentation, and a verifiable fetch manifest; fix the three indicator identities and methodology regimes. Establish a multi-episode recession/shock roster and a country/time holdout before registering a new bankruptcy question. A single 2007–08 crisis cohort is not independent event replication.
2. For Japan, acquire the **exact** first-registration FRED M2 and IMF gap inputs if a frozen rerun is intended; local BOJ M2 or a later OECD output-gap substitution requires a new ID and holdout. Implement the complete VECM/cointegration/comparator rule rather than rerunning a generic FE model.
3. For WTO, obtain accession dates, actual PMR entry-barrier observations, import and foreign-tariff channels, then preregister the exact staggered DiD and pre-trend choices before a new holdout. The saved TWFE coefficient cannot be promoted.
4. Preserve all 155 archived cases until a case-specific full-rule result passes registration, source, estimator, replication, and evidence-tier checks. Do not remove an estimator warning, copy a saved verdict, or grant school/policy/featured credit from this screen.

## Reproduction boundary

The case roster was derived from `engine/audits/hypothesis_conversion_funnel_2026-10-10.json`; the 131/24 split was verified from each saved run's loaded outcome, treatment, and control sources. First-registration versions came from `engine/preregistration_index.json` and `git show <spec_commit>:<path>`. The source-key checks above used the locally preserved main-checkout parquet files with only geography, year, null status, and recession indicator read. This audit did **not** modify either the consolidated primary worktree or the dirty main checkout and did not run or promote an estimator.
