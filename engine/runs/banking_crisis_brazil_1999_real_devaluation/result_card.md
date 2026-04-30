# Result card — banking_crisis_brazil_1999_real_devaluation

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 2 pending; 1 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** BRA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_depreciation_1999 | PENDING_DATA |  | `>= 35% depreciation` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 2 | imf_programme_1998 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_BRA_1998 |
| 3 | real_gdp_growth_disturbance | MET | 38.4 (1999) [pct_increase_from_baseline] | `>= 2 pp slowdown vs 1995-1997 average` |  |
| 4 | cpi_inflation_pickup | MET | 120 (2000) [pct_increase_from_baseline] | `>= 5 pp YoY rise from 1998 to 2000` |  |

## Claim

> Brazil's January 1999 abandonment of the crawling peg and devaluation of the real by >= 35% against USD, combined with the IMF programme negotiated in late 1998 and the legacy of the PROER bank-restructuring programme of 1995-1997, constitutes a canonical EM exchange-rate-anchor-failure case in which banking-system stress was managed without a Laeven-Valencia-coded systemic banking crisis. The hypothesis is that Brazil 1998-1999 meets the canonical multi-metric currency-crisis signature on at least 3 of 4 metrics, but does not satisfy the systemic-banking-crisis threshold.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_brazil_1999_real_devaluation.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
