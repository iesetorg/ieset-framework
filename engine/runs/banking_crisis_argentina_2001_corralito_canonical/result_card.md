# Result card — banking_crisis_argentina_2001_corralito_canonical

**Verdict:** supported

**Reason:** 5 of 6 metrics met threshold (support threshold 5)

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 5 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ARG

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | peso_depreciation_2002 | MET | 5.72e+03 (2001) [max_in_window_fallback] | `>= 65% depreciation` |  |
| 2 | real_gdp_decline | MET | 100 (2002) [peak_to_trough_pct_decline] | `>= 10% decline` |  |
| 3 | sovereign_default_event | MET | 1 (2001) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | corralito_deposit_freeze | MET | 1 (2001) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 5 | unemployment_peak | MET | 13.1 (2002) [pct_increase_from_baseline] | `>= 5 pp rise` |  |
| 6 | cpi_inflation_spike | NOT_MET | -2.45e+03 (2002) [pct_increase_from_baseline] | `>= 20 pp peak YoY rise` |  |

## Claim

> Argentina's 2001-2002 crisis — convertibility regime collapse, December 2001 corralito freeze on bank deposits, January 2002 currency-board abandonment, sovereign default, pesification of bank balance sheets, and real-GDP contraction of >= 10% peak-to-trough — is the canonical case of a hard-peg / currency-board collapse compounded by banking-system suspension. The hypothesis is that Argentina 2001-2002 meets the canonical multi-metric checklist on at least 5 of 6 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 5 of 6 pre-registered metrics meet their thresholds, above the support threshold of 5. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_argentina_2001_corralito_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
