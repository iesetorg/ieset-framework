# Result card — thailand_growth_health_services_shift_1990_2023

**Verdict:** supported

**Reason:** 4 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** THA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_pc_growth_sustained | MET | 2.99 (2023) [average_annual_growth_rate_value] | `average annual growth >= 2.5%` | average annual growth 1990-2023 = 2.993; threshold >=2.5 |
| 2 | under5_mortality_decline_large | MET | 75.1 (2023) [peak_to_trough_pct_decline] | `>= 70% decline` |  |
| 3 | life_expectancy_gain_large | MET | 12.6 (2021) [pct_increase_from_baseline] | `>= 10% increase` |  |
| 4 | services_employment_share_high | MET | 45.6 (2019) [max_in_window] | `>= 40% during 2019` |  |

## Claim

> Thailand's 1990-2023 development trajectory combined sustained real income growth, large child-mortality reductions, rising life expectancy, and a services-employment shift. The narrow test is whether Thailand clears at least three of four independent outcome thresholds over the period, using WDI vintages already present in the pipeline.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/thailand_growth_health_services_shift_1990_2023.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
