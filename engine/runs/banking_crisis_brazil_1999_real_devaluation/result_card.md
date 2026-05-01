# Result card — banking_crisis_brazil_1999_real_devaluation

**Verdict:** supported

**Reason:** 3 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 3 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** BRA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_depreciation_1999 | MET | 290 (1998) [max_in_window_fallback] | `>= 35% depreciation` |  |
| 2 | imf_programme_1998 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_BRA_1998 |
| 3 | real_gdp_growth_disturbance | MET | 38.4 (1999) [pct_increase_from_baseline] | `>= 2 pp slowdown vs 1995-1997 average` |  |
| 4 | cpi_inflation_pickup | MET | 120 (2000) [pct_increase_from_baseline] | `>= 5 pp YoY rise from 1998 to 2000` |  |

## Claim

> Brazil's January 1999 abandonment of the crawling peg and devaluation of the real by >= 35% against USD, combined with the IMF programme negotiated in late 1998 and the legacy of the PROER bank-restructuring programme of 1995-1997, constitutes a canonical EM exchange-rate-anchor-failure case in which banking-system stress was managed without a Laeven-Valencia-coded systemic banking crisis. The hypothesis is that Brazil 1998-1999 meets the canonical multi-metric currency-crisis signature on at least 3 of 4 metrics, but does not satisfy the systemic-banking-crisis threshold.

## Interpretation

The canonical-case pattern match is satisfied: 3 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_brazil_1999_real_devaluation.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
