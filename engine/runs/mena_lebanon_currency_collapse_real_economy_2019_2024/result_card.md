# Result card — mena_lebanon_currency_collapse_real_economy_2019_2024

**Verdict:** refuted

**Reason:** 3 metrics failed and 1 pending; cannot reach 5

Pre-registered rule: SUPPORT if >= 5 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 2 MET · 3 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** LBN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_pc_decline | NOT_MET | 30.4 (2023) [peak_to_trough_pct_decline] | `>40% decline` |  |
| 2 | lira_unofficial_depreciation | MET | 1.39e+04 (2023) [max_in_window_fallback] | `>95% depreciation` |  |
| 3 | cpi_inflation_peak | MET | 221 (2023) [max_in_window_fallback] | `>100% YoY at peak` |  |
| 4 | banking_sector_real_assets | PENDING_DATA |  | `>70% decline` | No LBN observations in loaded vintages |
| 5 | emigration_outflow_share | NOT_MET | -1.73e+04 (2024) [max_in_window] | `>10% of population` |  |
| 6 | electricity_supply_hours | NOT_MET | 100 (2021) [max_in_window_fallback] | `<4 hours per day` |  |

## Claim

> Lebanon's October-2019-onwards economic collapse (banking-sector freeze, BdL multi-rate regime, lira hyperinflation, GDP contraction, dollarisation reversal) produced one of the largest real-economy contractions of the 21st century, with World Bank estimating GDP shrinking ~58% peak-to-trough. The pre-registered claim is that, treating Lebanon as a single canonical-case multi-metric instance, at least 5 of 6 pre-registered extreme thresholds are met: (a) cumulative real-GDP-pc decline >40% from 2018 peak, (b) lira cumulative depreciation >95% in unofficial market, (c) CPI inflation >100% YoY at peak, (d) banking-sector total assets in real terms decline >70%, (e) emigration outflow >10% of pre-crisis population, (f) electricity supply hours per day fall below 4. The null counter-claim is that the cumulative effect is large but not at the canonical-extreme thresholds (e.g. emigration figure depends on unverified estimates).

## Interpretation

The canonical-case pattern match is not satisfied: only 2 of 6 metrics met their thresholds, below the support threshold of 5. Note that for canonical-case hypotheses, a refutation can indicate either that the hypothesis is genuinely weak, that the metric set is mis-calibrated (too strict), or that the data substrate has systematic gaps. Review the PENDING_DATA / PENDING_EVAL metrics before accepting the refutation.

## Steelman live concerns

See `hypotheses/steelman/mena_lebanon_currency_collapse_real_economy_2019_2024.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
