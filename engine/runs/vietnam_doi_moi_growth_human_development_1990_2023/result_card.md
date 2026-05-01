# Result card — vietnam_doi_moi_growth_human_development_1990_2023

**Verdict:** supported

**Reason:** 4 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** VNM

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_pc_growth_fast | MET | 5.23 (2023) [average_annual_growth_rate_value] | `average annual growth >= 4%` | average annual growth 1990-2023 = 5.235; threshold >=4 |
| 2 | under5_mortality_decline | MET | 65.5 (2023) [peak_to_trough_pct_decline] | `>= 60% decline` |  |
| 3 | trade_openness_high | MET | 183 (2022) [max_in_window] | `>= 150% during 2022` |  |
| 4 | services_employment_shift | MET | 39.5 (2023) [max_in_window] | `>= 35% during 2023` |  |

## Claim

> Vietnam's post-Doi Moi development path from 1990 to 2023 combined rapid real income growth, human-development gains, trade integration, and a labour-market shift toward services. The narrow test is whether Vietnam clears at least three of four independent outcome thresholds: average real GDP per-capita growth of at least 4% per year, at least a 60% decline in under-5 mortality, trade openness above 150% of GDP, and services employment reaching at least 35% of total employment.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/vietnam_doi_moi_growth_human_development_1990_2023.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
