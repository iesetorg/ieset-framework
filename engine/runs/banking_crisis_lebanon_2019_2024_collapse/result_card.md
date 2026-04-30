# Result card — banking_crisis_lebanon_2019_2024_collapse

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 5 more need resolution

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 4 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** LBN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_cumulative_decline | NOT_MET | 32.9 (2023) [peak_to_trough_pct_decline] | `>= 35% decline` |  |
| 2 | cpi_inflation_spike | PENDING_EVAL | 221 [max_loaded_value] | `>= 100% YoY peak` | count-based threshold requires event log; data not sufficient to auto-count |
| 3 | pound_depreciation | PENDING_DATA |  | `>= 90% nominal depreciation peak-to-trough` | No usable vintage for: imf:ENDA_XDC_USD_RATE |
| 4 | sovereign_default_event | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:LBN_DEFAULT_2020 |
| 5 | informal_capital_controls | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:LBN_CFM_2019 |
| 6 | bank_credit_to_gdp_decline | PENDING_DATA |  | `>= 50 pp of GDP decline` | No LBN observations in window 2019-2023 |

## Claim

> Lebanon's 2019-2024 banking collapse — informal capital controls, multi-tier exchange rates, sovereign default on Eurobonds in March 2020, and a real-GDP cumulative decline of >= 35% — constitutes a canonical case of a peg-plus-Ponzi- banking-system unwind in a small, dollarised, post-civil-war economy. The hypothesis is that Lebanon 2019-2024 meets the canonical multi-metric checklist on at least 5 of 6 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_lebanon_2019_2024_collapse.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
