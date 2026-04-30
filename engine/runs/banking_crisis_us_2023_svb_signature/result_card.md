# Result card — banking_crisis_us_2023_svb_signature

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 4 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | svb_signature_failure_dates | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: fred:SVB_SIGNATURE_FAILURE_2023 |
| 2 | btfp_facility_creation | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: fred:H41RESPPALDKNWW, fred:BTFP_2023 |
| 3 | regional_bank_equity_decline | PENDING_DATA |  | `>= 25% decline March-May 2023` | No usable vintage for: fred:WILLREITPR, fred:DJUSBK |
| 4 | large_uninsured_deposit_outflow | PENDING_DATA |  | `>= USD 200bn outflow over 8 weeks` | No usable vintage for: fred:DPSACBW027SBOG |
| 5 | real_gdp_growth_undisturbed | PENDING_EVAL |  | `annual growth >= 2% in 2023 (negative-control: episode did NOT propagate to macro)` | Non-tidy (needs custom parser): fred:GDPC1 |

## Claim

> The March 2023 US regional-banking distress — Silicon Valley Bank failure 10-Mar-2023, Signature Bank failure 12-Mar-2023, First Republic Bank failure 1-May-2023, plus the Bank Term Funding Program created 12-Mar-2023 — was a duration-mismatch / uninsured-deposit-flight event triggered by the 2022-2023 Fed-tightening cycle marking long-duration AFS securities below-water. The hypothesis is that the 2023 episode meets a tightly-scoped multi-metric checklist on at least 4 of 5 metrics WITHOUT producing a Laeven-Valencia-grade systemic outcome.

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_us_2023_svb_signature.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
