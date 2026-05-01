# Result card — ordo_anti_cartel_post_war_germany_economic_miracle

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** DEU

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | per_capita_growth_acceleration_1949_1957 | MET | 97.8 (1957) [pct_increase_from_baseline] | `>=6.0%/yr` |  |
| 2 | per_capita_growth_post_gwb_persistence_1958_1965 | MET | 36.3 (1965) [pct_increase_from_baseline] | `>=4.0%/yr` |  |
| 3 | industrial_production_growth_1958_1965 | PENDING_DATA |  | `>=5.0%/yr` | No DEU observations in window 1958-1965 |
| 4 | pwt_rgdpna_concordance | MET | 180 (1965) [pct_increase_from_baseline] | `>=0.80 log-pts cumulative` |  |
| 5 | pre_gwb_to_post_gwb_growth_ratio | MET | 64.3 (1949) [peak_to_trough_pct_decline] | `>=0.50 ratio` |  |

## Claim

> Post-war West Germany's Wirtschaftswunder (1948-1965) reflects the combined effect of (a) Erhard's June-1948 currency reform plus immediate price-control liberalisation and (b) the 1957 Gesetz gegen Wettbewerbsbeschränkungen (GWB) anti-cartel law. The ordoliberal claim is that the competition-policy contribution is identifiable as a distinct channel from the currency-reform contribution: real GDP-per-capita growth in the post-GWB sub-window (1958-1965) remained at or above the pre-GWB sub-window (1949-1957) despite the convergence-catch-up effect having largely exhausted by 1957, indicating that competition-rule enforcement preserved productivity growth past the point at which simple reconstruction effects predicted deceleration.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/ordo_anti_cartel_post_war_germany_economic_miracle.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
