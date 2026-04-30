# Result card — banking_crisis_us_sl_crisis_1986_1995

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_failures_count_peak | PENDING_DATA |  | `>= 200 institutions failed in a single year between 1988 and 1992` | No usable vintage for: fred:BKFTTLA01USA661N, fred:USNUM |
| 2 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded yes` | No usable vintage for: owid:systemic-banking-crises |
| 3 | real_house_price_regional_decline | PENDING_EVAL |  | `>= 15% peak-to-trough in BIS US RPPI` | Non-tidy (needs custom parser): bis:WS_SPP, fred:USSTHPI |
| 4 | rtc_creation_1989 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: fred:RTC_FIRREA_1989 |
| 5 | real_gdp_minor_disturbance | NOT_MET | 0 (1990) [pct_increase_from_baseline] | `>= 1 pp slowdown vs prior 5y average` |  |

## Claim

> The US Savings & Loan crisis of 1986-1995 — closure or assistance of >= 1,000 thrifts, Resolution Trust Corporation creation in 1989, FDIC bank failures peaking in 1988-1992, estimated taxpayer cost in the USD 100-200bn range, and a Laeven-Valencia coded systemic banking crisis 1988 — was a US-domestic banking crisis with limited GDP impact. The hypothesis is that S&L 1986-1995 meets a multi-metric checklist on at least 4 of 5 metrics tuned to the institution-level rather than macro-aggregate signature.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_us_sl_crisis_1986_1995.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
