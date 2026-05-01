# Result card — banking_crisis_ireland_2008_property_bust

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** IRL

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_house_price_decline | MET | 64.2 (2012) [peak_to_trough_pct_decline] | `>= 50% decline` |  |
| 2 | real_gdp_contraction | MET | 9.35 (2009) [peak_to_trough_pct_decline] | `>= 7% decline` |  |
| 3 | unemployment_rate_rise | MET | 695 (2011) [pct_increase_from_baseline] | `>= 9 pp rise` |  |
| 4 | government_debt_run_up | MET | 1.4e+05 (2013) [pct_increase_from_baseline] | `>= 70 pp of GDP rise` |  |
| 5 | troika_programme_entered | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:EFF_IRL_2010 |

## Claim

> The 2008-2013 Irish banking crisis was a property-credit-bust event in which the Anglo Irish Bank, Allied Irish Banks, and Bank of Ireland balance-sheet expansion during 2003-2007 produced a real-house-price peak-to-trough decline of >= 50%, a bank-rescue fiscal cost of >= 25% of GDP, an unemployment rate rise of >= 9 pp, and a Troika programme entry. The hypothesis is that the canonical multi-metric signature for Ireland is met across at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_ireland_2008_property_bust.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
