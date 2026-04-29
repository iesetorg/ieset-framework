# Result card — venezuela_chavismo_canonical_case_multi_metric

**Verdict:** supported

**Reason:** 9 of 10 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 10 metrics met; REFUTE if <= 3 met (impossible to hit support).

**Counts:** 9 MET · 0 NOT_MET · 0 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** VEN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | emigration_outflow_share_population | MET | 120 (2023) [pct_increase_from_baseline] | `>15% of 2013 population` |  |
| 2 | hyperinflation_cagan_threshold | PENDING_EVAL | 6.54e+04 [max_loaded_value] | `>=2 consecutive months of >50% m/m CPI` | count-based threshold requires event log; data not sufficient to auto-count |
| 3 | crude_oil_production_collapse | MET | 78.9 (2020) [peak_to_trough_pct_decline] | `>60% decline in monthly crude production` |  |
| 4 | hdi_absolute_decline | MET | 0.076 [absolute_decline] | `>0.05 absolute HDI decline` |  |
| 5 | extreme_poverty_rate | MET | 79.3 (2018) [max_in_window] | `>70% extreme poverty rate in any year` |  |
| 6 | under5_mortality_reversal | MET |  | `>20% increase in under-5 mortality rate from 2012 to any year 2017-2020` | event-count [max_value] = 26.2507 in 2017-2020; threshold >20 |
| 7 | real_minimum_wage_collapse_usd | MET | 100 (2022) [peak_to_trough_pct_decline] | `>90% loss of real minimum wage measured in constant USD` |  |
| 8 | electrical_grid_collapse | MET | 50 (2020) [pct_increase_from_baseline] | `>=3 documented nationwide blackouts of >24 hours` |  |
| 9 | food_insecurity_ipc_phase | MET | 32.6 (2018) [max_in_window] | `>20% of population in IPC Phase 3+ at any point` |  |
| 10 | currency_par_value_collapse | MET | 100 (2023) [peak_to_trough_pct_decline] | `>99.99% cumulative purchasing power loss vs USD` |  |

## Claim

> Venezuela's post-1999 socialist policy regime (Chávez 1999-2013 + Maduro 2013-present, characterised by FX controls, price controls, mass nationalisations, PDVSA politicisation, and 2014+ monetary financing of fiscal deficits) produced a canonical institutional and economic collapse that manifests as ≥7 of 10 pre-registered extreme-outcome metrics, each drawn from an independent data source and measuring a different causal layer. The canonical-case claim is that no non-war peacetime economy in the 2000-2024 window matches even 4 of these 10 thresholds simultaneously; Venezuela matches most. A refutation (≤3 metrics met) would indicate the framework's institutional-quality coding is overstated, or that Venezuela's collapse has been substantially exaggerated in the consensus record.

## Interpretation

The canonical-case pattern match is satisfied: 9 of 10 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/venezuela_chavismo_canonical_case_multi_metric.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
