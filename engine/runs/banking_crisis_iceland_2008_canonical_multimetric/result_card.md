# Result card — banking_crisis_iceland_2008_canonical_multimetric

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 3 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 2 MET · 1 NOT_MET · 2 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** ISL

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_assets_to_gdp_peak | PENDING_EVAL | 243 [max_loaded_value] | `>= 700% of GDP` | count-based threshold requires event log; data not sufficient to auto-count |
| 2 | krona_depreciation_2008_2009 | PENDING_DATA |  | `>= 50% nominal depreciation peak-to-trough` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 3 | real_gdp_peak_to_trough | MET | 10.4 (2010) [peak_to_trough_pct_decline] | `>= 8% peak-to-trough decline` |  |
| 4 | unemployment_rate_rise | MET | 157 (2010) [pct_increase_from_baseline] | `>= 5 pp rise from 2007 baseline` |  |
| 5 | imf_stand_by_arrangement_entered | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_ICL_2008 |
| 6 | sovereign_yield_spike_or_cds | NOT_MET | 12.9 (2009) [pct_increase_from_baseline] | `>= 500 bp at peak` |  |

## Claim

> The 2008 Icelandic banking collapse (failure of Glitnir, Landsbanki, and Kaupthing in October 2008) is a canonical case of a small-open-economy systemic banking crisis driven by external-funded balance-sheet expansion exceeding any plausible lender-of- last-resort capacity. The hypothesis is that the Iceland 2008 episode meets the canonical-case checklist with extreme metric values: at least 5 of 6 pre-registered metrics (bank-assets-to-GDP, ISK depreciation, real-GDP contraction, unemployment rise, IMF programme entry, sovereign-yield spike) hit thresholds well above the cross-country GFC norm.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_iceland_2008_canonical_multimetric.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
