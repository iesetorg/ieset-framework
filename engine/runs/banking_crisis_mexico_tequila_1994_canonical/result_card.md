# Result card — banking_crisis_mexico_tequila_1994_canonical

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** MEX

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | peso_depreciation_1994_1995 | PENDING_DATA |  | `>= 50% depreciation` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 2 | real_gdp_decline_1995 | NOT_MET | 5.91 (1995) [peak_to_trough_pct_decline] | `>= 6% decline` |  |
| 3 | imf_us_treasury_programme | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_MEX_1995 |
| 4 | systemic_banking_crisis_coded | PENDING_DATA |  | `coded yes` | No usable vintage for: owid:systemic-banking-crises |
| 5 | current_account_reversal | PENDING_EVAL | -0.415 [max_loaded_value] | `>= 5 pp of GDP swing 1994-1996` | count-based threshold requires event log; data not sufficient to auto-count |

## Claim

> Mexico's December-1994 Tequila Crisis — peso devaluation against the USD by >= 50%, IMF / US Treasury rescue package, real-GDP contraction of >= 6% in 1995, and a Laeven-Valencia-coded systemic banking crisis 1994-1996 — is the canonical EM-currency-and-banking-twin-crisis case of the early 1990s. The hypothesis is that Mexico 1994-1996 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_mexico_tequila_1994_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
