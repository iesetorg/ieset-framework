# Result card — russia_sanctions_2022_2025_economic_response_decomposition

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 4 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** RUS

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | gdp_shortfall_vs_march2022_forecast | PENDING_EVAL |  | `actual cumulative 2022-2024 GDP within +/- 4pp of MARCH-2022 IMF projection (i.e., damage materialised meaningfully but bounded)` | cross-country gap/ratio requires dedicated cross-country evaluator; data present |
| 2 | oil_revenue_rerouting_china_india_share | PENDING_DATA |  | `>=70% of seaborne crude exports to CHN+IND by 2024 (vs ~30% in 2021)` | No usable vintage for: owid:russian_oil_exports_destination |
| 3 | ruble_stabilisation_post_initial_collapse | PENDING_DATA |  | `RUB/USD by 2024-Q4 within 30% of 2021 baseline (i.e., partial recovery from 2022-03 trough but not full retracement)` | No usable vintage for: fred:DEXRUUS |
| 4 | technology_import_collapse | PENDING_DATA |  | `>=50% decline in tech-imports from G7 by 2024 vs 2021` | No usable vintage for: world_bank_wdi:NE.IMP.GNFS.KD |
| 5 | fiscal_buffer_nwf_drawdown | PENDING_DATA |  | `>40% decline in liquid NWF assets over the window` | No usable vintage for: cbr:nwf_liquid_assets |
| 6 | third_country_intermediation_turkey_uae | NOT_MET | 0 (2022) [pct_increase_from_baseline] | `>=50% cumulative trade increase with TUR+ARE+KAZ combined 2022-2024 vs 2021 baseline` |  |

## Claim

> Western sanctions on Russia 2022-2025 produced material but bounded economic damage — GDP contraction shallower than Western forecasters predicted in March 2022 — because oil-revenue rerouting (China + India + Turkey absorption of seaborne crude under the G7 price cap) and import-substitution from EAEU partners blunted the trade-shock impact, while the ruble stabilised after initial collapse via capital controls and a current-account surplus. The effective sanctions impact was real but smaller than the "isolation" rhetoric suggested, with binding effects concentrated in technology imports and long-run capital deepening.

## Interpretation

Verdict is **inconclusive (data gaps)** — 4 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/russia_sanctions_2022_2025_economic_response_decomposition.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
