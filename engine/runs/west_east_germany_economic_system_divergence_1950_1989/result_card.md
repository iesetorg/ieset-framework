# Result card — west_east_germany_economic_system_divergence_1950_1989

**Verdict:** supported

**Reason:** 11 of 11 metrics met threshold (support threshold 7)

Pre-registered rule: SUPPORT if >= 7 of 11 metrics met; REFUTE if <= 3 met (impossible to hit support).

**Counts:** 11 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** DEW

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_per_capita_ppp_ratio_1989 | MET | 2.6 (1989) [max_in_window] | `> 2.0 in any year` |  |
| 2 | consumer_goods_availability_wait_time | MET | 100 (1985) [max_in_window] | `> 10 in any year` |  |
| 3 | emigration_flow_pre_wall | MET | 19.4 (1961) [max_in_window] | `> 15 in any year` |  |
| 4 | telephone_penetration_gap | MET | 2.35 (1989) [max_in_window] | `> 2.0 in any year` |  |
| 5 | car_ownership_ratio | MET | 2.14 (1989) [max_in_window] | `> 1.5 in any year` |  |
| 6 | innovation_patent_filings | MET | 18 (1989) [max_in_window] | `> 10 in any year` |  |
| 7 | consumer_electronics_trade_balance | MET | 57.1 (1980) [peak_to_trough_pct_decline] | `> 5 in any year` |  |
| 8 | environmental_pollution_load | MET | 5.2 (1989) [max_in_window] | `> 2.0 in any year` |  |
| 9 | stasi_surveillance_intensity | MET | 15.4 (1988) [max_in_window] | `> 10 in any year` |  |
| 10 | post_1989_revealed_productivity_gap | MET | 62.5 (1990) [peak_to_trough_pct_decline] | `> 3.0 in any year` |  |
| 11 | post_reunification_transfer_scale | MET | 70 (2000) [peak_to_trough_pct_decline] | `> 1.5 in any year` |  |

## Claim

> Starting from comparable 1945 post-war conditions — same ethnicity, language, pre-war German institutional and industrial inheritance, and with the GDR inheriting a larger share of pre-war industrial capital in Saxony and Thuringia — the Federal Republic's Soziale Marktwirtschaft (Ordoliberal market economy with welfare state) versus the German Democratic Republic's planned economy with administered prices, state-enterprise production, and soft budget constraints produced by 1989 a canonical divergence that pattern-matches >=7 of 10 pre-registered extreme-outcome metrics, each drawn from a different publisher or methodology family. The canonical-case claim is that no other peacetime country pair separated for comparable duration from comparable 1945 starting conditions produced a divergence of this magnitude across this many independent outcome channels. A refutation (<=3 metrics met) would indicate that the consensus FRG/GDR gap was substantially overstated or that the framework's institutional-quality coding of market vs planned economies is mis-calibrated.

## Interpretation

The canonical-case pattern match is satisfied: 11 of 11 pre-registered metrics meet their thresholds, above the support threshold of 7. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/west_east_germany_economic_system_divergence_1950_1989.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
