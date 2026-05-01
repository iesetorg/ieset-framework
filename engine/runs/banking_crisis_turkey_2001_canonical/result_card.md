# Result card — banking_crisis_turkey_2001_canonical

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** TUR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | lira_depreciation_2001 | MET | 660 (2001) [max_in_window_fallback] | `>= 50% depreciation` |  |
| 2 | real_gdp_decline_2001 | MET | 6.05 (2001) [peak_to_trough_pct_decline] | `>= 5% decline` |  |
| 3 | imf_programme | MET | 1 (2001) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | systemic_banking_crisis_coded | MET | 1 (2001) [coded_yes_indicator_max] | `coded yes` | coded YES evaluated from binary event indicator |
| 5 | cpi_inflation_persistence | NOT_MET | 54.4 (2001) [max_in_window_fallback] | `>= 60% YoY peak` |  |

## Claim

> Turkey's February 2001 banking crisis — exchange-rate-based stabilisation collapse, TRL devaluation of >= 50% against USD, real-GDP contraction of >= 5%, large IMF programme, and Banking Regulation and Supervision Agency takeover of failed banks — is a canonical case of an EM exchange-rate-anchor disinflation programme failing through the banking-system channel. The hypothesis is that Turkey 2001 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_turkey_2001_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
