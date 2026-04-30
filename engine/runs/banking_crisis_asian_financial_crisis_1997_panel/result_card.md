# Result card — banking_crisis_asian_financial_crisis_1997_panel

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 3 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** THA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | nominal_currency_depreciation_peak | PENDING_DATA |  | `>= 30% nominal depreciation in at least 4 of 5 countries` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 2 | real_gdp_decline_1998 | MET | 7.63 (1998) [peak_to_trough_pct_decline] | `>= 5% peak-to-trough in at least 4 of 5 countries` |  |
| 3 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded in at least 4 of 5 countries` | No usable vintage for: owid:systemic-banking-crises |
| 4 | imf_programme_entered | PENDING_DATA |  | `yes in at least 4 of 5 countries (THA, IDN, KOR, PHL definite; MYS opted out — 4 of 5 expected)` | No usable vintage for: imf:SBA_PROGRAMMES_1997_1998 |
| 5 | current_account_reversal | MET | 164 (1996) [peak_to_trough_pct_decline] | `>= 8 pp of GDP swing in at least 4 of 5 countries` |  |

## Claim

> The 1997-1998 Asian Financial Crisis affected a tightly-clustered group of east-Asian economies (Thailand, Indonesia, Korea, Malaysia, Philippines) through a common pattern of currency-peg collapse, foreign-currency-denominated bank-and-corporate balance-sheet distress, large IMF programmes, and sharp output contractions. The hypothesis is that across the five-country panel, a multi-metric checklist of currency depreciation, real-GDP contraction, banking-crisis coding, IMF programme entry, and current-account reversal is met in at least 4 of 5 countries on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_asian_financial_crisis_1997_panel.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
