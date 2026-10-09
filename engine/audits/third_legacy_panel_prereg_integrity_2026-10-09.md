# Third legacy panel cohort: registration and verdict-integrity audit

Date: 2026-10-09. **Registration review only.** No new outcome values, null masks, coefficients, verdicts, or run artifacts were opened or created for this cohort.

## Historical boundary and old-result disclosure

The old run commit `e786a95e676c9d6283c123682d43bf54dbacd73b` contains each selected old spec and first-run diagnostics. Its `scripts/run_panel_fe.py` filters to the spec's country roster before fitting. Every selected old spec has the same explicit 40 ISO3 countries. The eight new IDs exclude all 40, including old countries without fitted rows. The new runner checks the historical spec, exact treatment/outcome source pair, fitted observation/country counts, first-run verdict and inferred direction, and the historical runner's country filter. This proves separation from each named old fit, not independence from every other IESET study.

| New measured pair | Old ID | First old result | First direction |
| --- | --- | --- | --- |
| Services employment share → real private consumption per-person growth | `private_sector_job_creation_consumption` | PARTIAL | + |
| WGI regulatory quality → labor-force participation | `portable_benefits_market_flexibility` | PARTIAL | + |
| Real GDP per person → physician density | `medical_migration_market_opportunity` | SUPPORTED | + |
| WGI government effectiveness → gross tertiary enrollment | `tertiary_autonomy_research_output` | PARTIAL | + |
| WGI government effectiveness → electricity access | `state_capacity_market_infrastructure_complement` | PARTIAL | + |
| Government final-consumption share → electricity access | `state_monopoly_infrastructure_cost_overrun` | PARTIAL | - |
| WGI regulatory quality → urban population share | `market_urbanization_slum_reduction` | PARTIAL | + |
| Government final-consumption share → high-tech share of manufactured exports | `incumbent_subsidy_innovation_drag` | PARTIAL | - |

Each new claim is confined to the named measured pair. WGI scores are perceptions-based composites; the WDI measures do not directly observe the old claims about portable benefits, medical migration, university autonomy, state-market complementarity, monopoly cost overruns, slum reduction, or subsidies. The [World Bank WGI documentation](https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation) and indicator pages for [services employment](https://data.worldbank.org/indicator/SL.SRV.EMPL.ZS), [tertiary enrollment](https://data.worldbank.org/indicator/SE.TER.ENRR), [electricity access](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS), and [urban population share](https://data.worldbank.org/indicator/SP.URB.TOTL.IN.ZS) give the source meanings.

The eight tests share a fixed two-sided Bonferroni cutoff of `0.10/8 = 0.0125` for either supported or opposite-sign refuted direction, country/year effects and country-clustered uncertainty. The complete-case gate is 800 pairs, 50 countries, and five treatment years per country. `school_score_credit: 0` and `school_score_eligible: false` are pinned in every new threshold, and the runner writes a zero-credit correction in each eventual diagnostic. No school links are registered. Key-only preflight, which read country/year columns and source hashes but no values or null masks, found 4,175 eligible key pairs and 167 countries for each case; these are **upper bounds**, not complete-case counts or evidence of support.

## Legacy sign-inference defect and exclusions

The later refresh commit `0265cebb33d0ef5e98fd44b09a59717a89003522` changed many old result directions without changing their claims. Its sign parser searched up to 80 characters after `coefficient` for `< 0`. In the generic rule “coefficient has the predicted sign at p<0.10”, that expression could match the **p-value threshold** instead of a coefficient condition. The current parser requires the inequality to be attached to the coefficient token; stored legacy results have not been rewritten. This is an audit trigger, not a corrected old verdict.

The committed [legacy sign audit](legacy_panel_sign_inference_2026-10-09.md) fixes the selection to **64 current generic-rule `run_panel_fe` records** that also appear at `e786a95`: 57 inferred directions and 22 verdict labels changed between historical and stored outputs. Six changed from REFUTED to SUPPORTED: `dialysis_market_competition_outcome_quality`, `female_lfp_market_opportunity`, `financial_market_depth_productivity`, `generic_substitution_mandate_savings_no_harm`, `health_savings_account_preventive_spending`, and `market_income_school_completion`. These are metadata comparisons; every disputed claim still requires its own direction adjudication before any old verdict is used as validated evidence.

The second-wave pair screen did not flag this direction issue. Three otherwise proposed old cases were excluded from this cohort because their inferred direction changed between first run and current result, even though their PARTIAL verdict label did not: `payroll_tax_labor_force_participation` (`+` to `-`), `market_openness_multidimensional_prosperity_1995_2024` (`+` to `-`), and `labor_market_flexibility_employment_qol` (`+` to `-`). `market_income_school_completion` was first REFUTED under `+` and later relabeled SUPPORTED under `-`; `market_reform_female_education` was first INCONCLUSIVE_DATA_PENDING under `+` and later relabeled SUPPORTED under `-`. Neither education case was selected.

Alias-aware comparison to strict preregistrations also excluded government-consumption share → GDP per person (`welfare_architecture_market_openness_nordic`) and WGI regulatory quality → high-tech export share (`market_order_regulatory_quality_high_tech_exports_panel`). The screening script had missed these because those strict tests use additional variables or the `GOV_WGI_` source alias. The eight selected pairs have no such same-pair strict registration in the checked index.

## Custody boundary

All eight new specs, steelmen, and `scripts/run_third_legacy_panel_geographic_holdouts_v2.py` must first appear unchanged in one Git commit with no corresponding run artifact. The runner refuses value loading until that first-addition condition is met. A later run needs source-SHA/manifest verification, complete-case gate, full artifact creation, exact read-only replay, evidence-tier regeneration, and public-funnel verification before counting any graduation. The key-only preflight was successful; no result is claimed here.
