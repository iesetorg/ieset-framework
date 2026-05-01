# Result card — banking_crisis_russia_1998_default_canonical

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** RUS

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | ruble_depreciation_1998 | MET | 841 (1998) [max_in_window_fallback] | `>= 60% depreciation` |  |
| 2 | real_gdp_decline | MET | 100 (1998) [peak_to_trough_pct_decline] | `>= 5% peak-to-trough decline` |  |
| 3 | sovereign_default_event | MET | 1 (1998) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | systemic_banking_crisis_coded | PENDING_DATA |  | `coded yes` | No RUS observations in loaded vintages |
| 5 | cpi_inflation_spike | MET | 210 (1999) [pct_increase_from_baseline] | `>= 50 pp YoY peak rise` |  |

## Claim

> The August 1998 Russian crisis — domestic-currency sovereign default, ruble devaluation of >= 60% against USD, real-GDP contraction of >= 5%, banking-system collapse with widespread bank failures, and IMF programme entry — is the canonical EM sovereign-and-banking-twin-default case of the late 1990s. The hypothesis is that Russia 1998 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_russia_1998_default_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
