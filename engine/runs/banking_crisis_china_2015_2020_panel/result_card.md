# Result card — banking_crisis_china_2015_2020_panel

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 1 pending; 1 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 1 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** CHN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | shanghai_stock_index_2015_decline | PENDING_DATA |  | `>= 40% peak-to-trough decline June-2015 to Feb-2016` | No usable vintage for: fred:CHNSCITRD, fred:SHCOMP |
| 2 | real_house_price_decline_tier_2_3 | MET | 20.7 (2024) [peak_to_trough_pct_decline] | `>= 8% nominal decline in BIS WS_SPP` |  |
| 3 | bank_credit_to_gdp_extreme_run_up | NOT_MET | 52.6 (2016) [pct_increase_from_baseline] | `>= 70 pp of GDP rise from 2008 to 2017 peak` |  |
| 4 | laeven_valencia_no_systemic_coding | MET | 0 (2015) [coded_no_indicator_max] | `coded NO — supports the 'managed under capital controls' framing` | coded NO evaluated from binary event indicator |

## Claim

> China's 2015 stock-market crash and the 2020-2024 property-sector deleveraging episode (Evergrande default August 2021, Country Garden distress August 2023, the "three red lines" macroprudential framework introduced 2020) constitute a sustained financial-stress episode characterised by extreme equity volatility 2015-2016, real residential property price decline >= 10% in tier-2/3 cities 2021-2024, and developer-bond defaults exceeding RMB 1 trillion cumulative. The hypothesis is that China 2015-2024 meets a multi-metric financial-stress checklist on at least 3 of 4 metrics WITHOUT producing a Laeven-Valencia-coded systemic banking crisis.

## Interpretation

Verdict is **inconclusive (data gaps)** — 1 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_china_2015_2020_panel.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
