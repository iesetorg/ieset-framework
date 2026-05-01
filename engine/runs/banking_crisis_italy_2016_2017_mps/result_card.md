# Result card — banking_crisis_italy_2016_2017_mps

**Verdict:** supported

**Reason:** 4 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ITA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_npl_ratio_peak | MET | 18.1 (2015) [max_in_window_fallback] | `>= 16% gross NPL ratio` |  |
| 2 | mps_precautionary_recap | MET | 1 (2017) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 3 | veneto_banks_resolution | MET | 1 (2017) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | bank_credit_to_gdp_decline | MET | 18.3 (2018) [peak_to_trough_pct_decline] | `>= 15 pp of GDP decline` |  |

## Claim

> Italy's 2016-2017 banking-distress episode — Banca Monte dei Paschi di Siena precautionary recapitalisation in July 2017, Veneto-banks resolution in June 2017, and a peak system-wide non-performing-loan ratio above 17% — represents a protracted-NPL-overhang post-GFC banking distress case that did NOT meet the canonical full-systemic-banking-crisis threshold but DID require multiple state-aid resolution events. The hypothesis is that Italy 2016-2017 meets a deliberately- weaker multi-metric checklist on at least 3 of 4 metrics, while explicitly NOT meeting the full Laeven-Valencia systemic-crisis threshold.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_italy_2016_2017_mps.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
