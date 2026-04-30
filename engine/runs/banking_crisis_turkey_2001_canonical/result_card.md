# Result card — banking_crisis_turkey_2001_canonical

**Verdict:** inconclusive (data gaps)

**Reason:** 1 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 1 MET · 0 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** TUR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | lira_depreciation_2001 | PENDING_DATA |  | `>= 50% depreciation` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 2 | real_gdp_decline_2001 | MET | 6.05 (2001) [peak_to_trough_pct_decline] | `>= 5% decline` |  |
| 3 | imf_programme | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_TUR_2001 |
| 4 | systemic_banking_crisis_coded | PENDING_DATA |  | `coded yes` | No usable vintage for: owid:systemic-banking-crises |
| 5 | cpi_inflation_persistence | PENDING_EVAL | 54.4 [max_loaded_value] | `>= 60% YoY peak` | count-based threshold requires event log; data not sufficient to auto-count |

## Claim

> Turkey's February 2001 banking crisis — exchange-rate-based stabilisation collapse, TRL devaluation of >= 50% against USD, real-GDP contraction of >= 5%, large IMF programme, and Banking Regulation and Supervision Agency takeover of failed banks — is a canonical case of an EM exchange-rate-anchor disinflation programme failing through the banking-system channel. The hypothesis is that Turkey 2001 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_turkey_2001_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
