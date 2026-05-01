# Result card — banking_crisis_latvia_2008_parex

**Verdict:** supported

**Reason:** 5 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 5 MET · 0 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** LVA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_decline | MET | 100 (2009) [peak_to_trough_pct_decline] | `>= 20% decline` |  |
| 2 | unemployment_rise | MET | 399 (2010) [pct_increase_from_baseline] | `>= 13 pp rise` |  |
| 3 | imf_eu_programme | MET | 1 (2008) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 4 | parex_nationalisation | MET | 1 (2008) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 5 | bank_credit_to_gdp_decline | MET | 44.9 (2014) [peak_to_trough_pct_decline] | `>= 30 pp of GDP decline` |  |

## Claim

> Latvia's 2008-2010 banking crisis — Parex Banka nationalisation in November 2008, EUR-peg defence, EUR 7.5bn IMF / EU programme, real-GDP cumulative decline of >= 20% peak-to-trough, and unemployment-rate rise of >= 13 pp — is a canonical small-open-economy hard-peg-defence + banking-rescue case from the GFC era. The hypothesis is that Latvia 2008-2010 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 5 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_latvia_2008_parex.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
