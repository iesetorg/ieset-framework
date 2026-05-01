# Result card — banking_crisis_vietnam_2012_2015_restructuring

**Verdict:** supported

**Reason:** 3 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 3 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** VNM

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | bank_npl_ratio_peak | NOT_MET | 3.5 (2014) [max_in_window_fallback] | `>= 4% reported NPL ratio` |  |
| 2 | vamc_created_2013 | MET | 1 (2013) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 3 | zero_vnd_bank_acquisitions_2015 | MET | 3 (2015) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | real_gdp_growth_undisturbed | MET | 5.5 (2015) [annual_growth_rate_value] | `annual growth >= 5% in each year (negative-control: contained restructuring)` | annual growth values: 2012=5.505, 2013=5.554, 2014=6.422, 2015=6.987; threshold each >=5 |

## Claim

> Vietnam's 2012-2015 banking-sector restructuring — Vietnam Asset Management Company (VAMC) created July 2013, NPL ratio peak above 4%, mandatory mergers of weak banks, and forced central-bank acquisition of three commercial banks at zero VND in 2015 — represents a controlled-resolution emerging-market banking distress event without a full systemic crisis. The hypothesis is that Vietnam 2012-2015 meets a deliberately- narrow multi-metric checklist on at least 3 of 4 metrics WITHOUT producing a Laeven-Valencia coded crisis or a real-GDP recession.

## Interpretation

The canonical-case pattern match is satisfied: 3 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_vietnam_2012_2015_restructuring.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
