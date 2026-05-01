# Result card — banking_crisis_mexico_tequila_1994_canonical

**Verdict:** refuted

**Reason:** 2 metrics failed and 2 pending; cannot reach 4

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 1 MET · 2 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** MEX

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | peso_depreciation_1994_1995 | MET | 292 (1994) [max_in_window_fallback] | `>= 50% depreciation` |  |
| 2 | real_gdp_decline_1995 | NOT_MET | 5.91 (1995) [peak_to_trough_pct_decline] | `>= 6% decline` |  |
| 3 | imf_us_treasury_programme | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_MEX_1995 |
| 4 | systemic_banking_crisis_coded | PENDING_DATA |  | `coded yes` | No usable vintage for: owid:systemic-banking-crises |
| 5 | current_account_reversal | NOT_MET | -0.415 (1995) [max_in_window_fallback] | `>= 5 pp of GDP swing 1994-1996` |  |

## Claim

> Mexico's December-1994 Tequila Crisis — peso devaluation against the USD by >= 50%, IMF / US Treasury rescue package, real-GDP contraction of >= 6% in 1995, and a Laeven-Valencia-coded systemic banking crisis 1994-1996 — is the canonical EM-currency-and-banking-twin-crisis case of the early 1990s. The hypothesis is that Mexico 1994-1996 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is not satisfied: only 1 of 5 metrics met their thresholds, below the support threshold of 4. Note that for canonical-case hypotheses, a refutation can indicate either that the hypothesis is genuinely weak, that the metric set is mis-calibrated (too strict), or that the data substrate has systematic gaps. Review the PENDING_DATA / PENDING_EVAL metrics before accepting the refutation.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_mexico_tequila_1994_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
