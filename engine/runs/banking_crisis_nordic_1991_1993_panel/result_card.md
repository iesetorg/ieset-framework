# Result card — banking_crisis_nordic_1991_1993_panel

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 3 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** NOR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_credit_to_gdp_run_up | PENDING_DATA |  | `>= 25 pp of GDP rise pre-crisis in all three countries` | No NOR observations in window 1985-1990 |
| 2 | real_house_price_decline | PENDING_DATA |  | `>= 25% decline in at least 2 of 3 countries` | No usable vintage for: jst:hpnom; Non-tidy (needs custom parser): bis:WS_SPP |
| 3 | real_gdp_contraction | MET | 15 (1989) [peak_to_trough_pct_decline] | `>= 5% decline in at least 2 of 3 countries` |  |
| 4 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded yes in all 3 countries` | No usable vintage for: owid:systemic-banking-crises |
| 5 | unemployment_rate_rise | MET | 16.6 (1995) [pct_increase_from_baseline] | `>= 6 pp rise in at least 2 of 3 countries` |  |

## Claim

> The 1988-1993 Nordic banking crises (Norway 1988-1991, Sweden 1991-1992, Finland 1991-1993) are a canonical post-deregulation credit-boom-bust panel. Following the mid-1980s liberalisation of credit and capital markets, all three countries experienced bank-credit-to-GDP run-up of >= 25 pp, real-house-price decline of >= 25%, real-GDP contraction of >= 5%, large bank rescues / nationalisations, and Laeven-Valencia banking-crisis coding. The hypothesis is that the canonical multi-metric pattern is met across at least 3 of 3 countries on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_nordic_1991_1993_panel.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
