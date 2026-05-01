# Result card — fiscal_dominance_japan_debt_non_crisis

**Verdict:** inconclusive (data gaps)

**Reason:** 3 metrics met, 2 pending; 1 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 3 MET · 0 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** JPN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | debt_to_gdp_threshold_breach | MET | 179 (2010) [min_level_in_window] | `>150% sustained 2010-2024` | min_level_in_window = 178.600; threshold >150 |
| 2 | cpi_inflation_below_persistent_threshold | MET | 3.27 (1991) [max_yoy_pct_change_in_window] | `<4% persistent across 1990-2024 (max ~3% transient post-COVID)` | max_yoy_pct_change_in_window = 3.273; threshold <4 |
| 3 | jgb_10y_yield_below_crisis_band | PENDING_DATA |  | `<5% across 1990-2024 (max ~1.5% in early 1990s, peaked ~1.7% in 2025)` | No usable vintage for: oecd:OECD.SDD.STES,DSD_KEI@DF_KEI,4.0 |
| 4 | jpy_trade_weighted_index_no_collapse | MET | 41.7 (1990) [peak_to_trough_pct_decline] | `no >50% REER decline in any 12-month window 1990-2024` |  |
| 5 | monetary_policy_independence_preserved | PENDING_DATA |  | `BoJ retains operational policy autonomy across 1990-2024 per qualitative coding` | No usable vintage for: boj:policy_governance_record, academic:bof_independence_index |

## Claim

> Japan post-1990 has run gross public-debt-to-GDP ratios from ~70% rising to ~250%, the highest sustained level in the OECD record, WITHOUT triggering inflation, currency collapse, sovereign-spread blowout, or fiscal-dominance-induced loss of monetary control. This case is a counter-example to the Sargent-Wallace 1981 "unpleasant monetarist arithmetic" prediction that high debt-to-GDP under monetary independence forces eventual monetisation and inflation. The post-Keynesian / MMT reading is that for a sovereign currency issuer with deep domestic savings absorption, the debt-stock constraint is a political-economy constraint about real-resource allocation, not a market-discipline constraint about solvency. The hypothesis tests whether Japan's debt path 1990-2024 violates the Sargent-Wallace prediction at standard significance, and whether inflation, JGB yields, and JPY trade-weighted index remained within non-crisis bands across the period.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/fiscal_dominance_japan_debt_non_crisis.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
