# Result card — banking_crisis_iceland_2008_canonical_multimetric

**Verdict:** refuted

**Reason:** 2 metrics failed and 0 pending; cannot reach 5

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 4 MET · 2 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ISL

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_assets_to_gdp_peak | NOT_MET | 243 (2007) [max_in_window_fallback] | `>= 700% of GDP` |  |
| 2 | krona_depreciation_2008_2009 | MET | 169 (2007) [max_in_window_fallback] | `>= 50% nominal depreciation peak-to-trough` |  |
| 3 | real_gdp_peak_to_trough | MET | 10.4 (2010) [peak_to_trough_pct_decline] | `>= 8% peak-to-trough decline` |  |
| 4 | unemployment_rate_rise | MET | 1.64e+03 (2008) [pct_increase_from_baseline] | `>= 5 pp rise from 2007 baseline` |  |
| 5 | imf_stand_by_arrangement_entered | MET | 1 (2008) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 6 | sovereign_yield_spike_or_cds | NOT_MET | 12.9 (2009) [pct_increase_from_baseline] | `>= 500 bp at peak` |  |

## Claim

> The 2008 Icelandic banking collapse (failure of Glitnir, Landsbanki, and Kaupthing in October 2008) is a canonical case of a small-open-economy systemic banking crisis driven by external-funded balance-sheet expansion exceeding any plausible lender-of- last-resort capacity. The hypothesis is that the Iceland 2008 episode meets the canonical-case checklist with extreme metric values: at least 5 of 6 pre-registered metrics (bank-assets-to-GDP, ISK depreciation, real-GDP contraction, unemployment rise, IMF programme entry, sovereign-yield spike) hit thresholds well above the cross-country GFC norm.

## Interpretation

The canonical-case pattern match is not satisfied: only 4 of 6 metrics met their thresholds, below the support threshold of 5. Note that for canonical-case hypotheses, a refutation can indicate either that the hypothesis is genuinely weak, that the metric set is mis-calibrated (too strict), or that the data substrate has systematic gaps. Review the PENDING_DATA / PENDING_EVAL metrics before accepting the refutation.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_iceland_2008_canonical_multimetric.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
