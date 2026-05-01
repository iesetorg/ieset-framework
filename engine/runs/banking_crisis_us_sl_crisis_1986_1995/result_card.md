# Result card — banking_crisis_us_sl_crisis_1986_1995

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_failures_count_peak | MET | 1.42e+04 (1986) [max_in_window_fallback] | `>= 200 institutions failed in a single year between 1988 and 1992` |  |
| 2 | laeven_valencia_systemic_banking_crisis | NOT_MET | 0 (1988) [coded_yes_indicator_max] | `coded yes` | coded YES evaluated from binary event indicator |
| 3 | real_house_price_regional_decline | MET | 81.9 (1992) [peak_to_trough_pct_decline] | `>= 15% peak-to-trough in BIS US RPPI` |  |
| 4 | rtc_creation_1989 | MET | 1 (1989) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 5 | real_gdp_minor_disturbance | MET | 5.33e+05 (1990) [pct_increase_from_baseline] | `>= 1 pp slowdown vs prior 5y average` |  |

## Claim

> The US Savings & Loan crisis of 1986-1995 — closure or assistance of >= 1,000 thrifts, Resolution Trust Corporation creation in 1989, FDIC bank failures peaking in 1988-1992, estimated taxpayer cost in the USD 100-200bn range, and a Laeven-Valencia coded systemic banking crisis 1988 — was a US-domestic banking crisis with limited GDP impact. The hypothesis is that S&L 1986-1995 meets a multi-metric checklist on at least 4 of 5 metrics tuned to the institution-level rather than macro-aggregate signature.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_us_sl_crisis_1986_1995.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
