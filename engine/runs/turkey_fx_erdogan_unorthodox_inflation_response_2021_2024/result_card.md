# Result card — turkey_fx_erdogan_unorthodox_inflation_response_2021_2024

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 5 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** TUR

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | lira_dollar_depreciation_2021_2023 | PENDING_DATA |  | `>60% depreciation in TRY/USD over the window` | No usable vintage for: fred:DEXTUUS |
| 2 | cpi_inflation_peak_2022 | PENDING_DATA |  | `>75% YoY peak` | No usable vintage for: tuik:cpi_yoy_headline |
| 3 | tcmb_policy_rate_minus_cpi_real_rate_trough | PENDING_DATA |  | `<-50pp at trough` | No usable vintage for: tcmb:one_week_repo, tuik:cpi_yoy_headline |
| 4 | post_reversal_disinflation_2024 | PENDING_DATA |  | `>25pp decline in CPI YoY peak-to-2024-12` | No usable vintage for: tuik:cpi_yoy_headline |
| 5 | fx_reserves_decline_swaps | PENDING_DATA |  | `net reserves ex-swaps below -50bn USD at trough` | No usable vintage for: tcmb:international_reserves_net_ex_swaps |

## Claim

> Erdogan's "unorthodox" doctrine 2021-2023 — repeated TCMB rate cuts during accelerating inflation under his Islamist-finance theory that high rates cause inflation — produced a textbook monetary-policy failure: lira collapse, inflation-expectations de-anchoring, and CPI peaking above 85% YoY before the post-election 2023 reversal under Erkan/Karahan brought rates from 8.5% to 50% and slowly re-anchored expectations.

## Interpretation

Verdict is **inconclusive (data gaps)** — 5 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/turkey_fx_erdogan_unorthodox_inflation_response_2021_2024.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
