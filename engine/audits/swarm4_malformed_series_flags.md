# Swarm-4 follow-up: malformed series-ID citations to fix

Surfaced by Swarm 4 (manifest coverage agent). These hypothesis YAMLs cite series IDs that don't resolve cleanly in their declared publisher's fetcher. Fix in a separate cleanup pass after Wave A merges — they're not template/manifest issues, they're free-text typos in `variables.*.source` strings.

| Hypothesis | Citation | Issue | Suggested fix |
|---|---|---|---|
| `labour/minimum_wage_employment_effect_us_states.yaml:53` | `fred:state_GDP` | Not a real FRED ID | Use per-state series like `fred:NYNGSP`, `fred:CANGSP`, etc. |
| `labour/minimum_wage_above_median_employment_teen_effects.yaml:79` | `fred:regional_GDP` | Not a real FRED ID | Use per-region BEA series via FRED |
| `institutional_quality/bukele_mass_incarceration_homicide_impact_2019_2024.yaml:47` | `unodc:VC.IHR.PSRC.P5` | That's a World Bank WDI code, not UNODC | Use `unodc:intentional_homicide` |
| `growth/bukele_fdi_gdp_investment_climate_2019_2024.yaml:66` | `unodc:VC.IHR.PSRC.P5` | Same | Same |
| `growth/el_salvador_bukele_gdp_crime_tradeoff_2019_2024.yaml:63` | `unodc:homicide_rate` | Wrong series_id | Use `unodc:intentional_homicide` |
| `monetary/hyperinflation_requires_fiscal_dominance.yaml:40` | `ilzetzki_reinhart_rogoff:exchange_rate_regime_classification` | Wrong series_id | Use `ilzetzki_reinhart_rogoff:era_classification_monthly_1940_2019` |
| `distribution/lula_bolsa_familia_poverty_reduction_decomposition_2003_2010.yaml:51` | `wid:bottom40 share` | Free-text label, not a series_id | Use `wid:wid_all` then filter in-script |
| `monetary/qe_asset_inflation_vs_cpi_divergence_post_2008.yaml:50` | `boj:MA` | Ambiguous between money_stock_m2 / monetary_base | Author should pick one |
| `institutional_quality/venezuela_chavismo_canonical_case_multi_metric.yaml:89` | `opec:monthly_oil_market_report` | Wrong publication (only ASB is supported) | Use `opec:asb_full` |
| `growth/nationalisation_investment_productivity_decline_venezuela.yaml:43` | `opec:monthly_oil_market_report` | Same | Same |

**Important caveat from swarm 4:** The `audit_runnability` script treats a publisher as "missing" only when there are zero parquet vintages on disk (`data/vintages/<pub>/*.parquet`). So manifest expansion alone won't drop the `NEEDS_DATA` count — the data still has to be *fetched*. For `boj`, `opec`, `wid` (manual-drop publishers), source files need to be placed in `data/manual/<pub>/` before the fetcher will succeed.
