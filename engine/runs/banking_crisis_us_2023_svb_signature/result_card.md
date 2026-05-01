# Result card — banking_crisis_us_2023_svb_signature

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | svb_signature_failure_dates | MET | 1 (2023) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 2 | btfp_facility_creation | MET | 8.01e+04 (2023) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 3 | regional_bank_equity_decline | PENDING_DATA |  | `>= 25% decline March-May 2023` | No usable vintage for: fred:WILLREITPR, fred:DJUSBK |
| 4 | large_uninsured_deposit_outflow | MET | 437 (2023) [max_8w_outflow_bn] | `>= USD 200bn outflow over 8 weeks` | max 8-week outflow 437.234bn in 2023-03 to 2023-05; threshold >= 200bn |
| 5 | real_gdp_growth_undisturbed | MET | 2.93 (2023) [annual_yoy_pct_growth] | `annual growth >= 2% in 2023 (negative-control: episode did NOT propagate to macro)` | annual growth values: 2023=2.934; threshold each >=2 |

## Claim

> The March 2023 US regional-banking distress — Silicon Valley Bank failure 10-Mar-2023, Signature Bank failure 12-Mar-2023, First Republic Bank failure 1-May-2023, plus the Bank Term Funding Program created 12-Mar-2023 — was a duration-mismatch / uninsured-deposit-flight event triggered by the 2022-2023 Fed-tightening cycle marking long-duration AFS securities below-water. The hypothesis is that the 2023 episode meets a tightly-scoped multi-metric checklist on at least 4 of 5 metrics WITHOUT producing a Laeven-Valencia-grade systemic outcome.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_us_2023_svb_signature.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
