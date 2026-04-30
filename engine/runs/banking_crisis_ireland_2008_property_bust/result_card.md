# Result card — banking_crisis_ireland_2008_property_bust

**Verdict:** inconclusive (data gaps)

**Reason:** 3 metrics met, 2 pending; 1 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 3 MET · 0 NOT_MET · 1 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** IRL

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_house_price_decline | PENDING_EVAL |  | `>= 50% decline` | Non-tidy (needs custom parser): bis:WS_SPP |
| 2 | real_gdp_contraction | MET | 9.35 (2009) [peak_to_trough_pct_decline] | `>= 7% decline` |  |
| 3 | unemployment_rate_rise | MET | 128 (2012) [pct_increase_from_baseline] | `>= 9 pp rise` |  |
| 4 | government_debt_run_up | MET | 397 (2012) [pct_increase_from_baseline] | `>= 70 pp of GDP rise` |  |
| 5 | troika_programme_entered | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:EFF_IRL_2010 |

## Claim

> The 2008-2013 Irish banking crisis was a property-credit-bust event in which the Anglo Irish Bank, Allied Irish Banks, and Bank of Ireland balance-sheet expansion during 2003-2007 produced a real-house-price peak-to-trough decline of >= 50%, a bank-rescue fiscal cost of >= 25% of GDP, an unemployment rate rise of >= 9 pp, and a Troika programme entry. The hypothesis is that the canonical multi-metric signature for Ireland is met across at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 1 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_ireland_2008_property_bust.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
