# Result card — china_zero_covid_2022_2023_demand_collapse_recovery

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 5 pending; 4 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 6 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 1 NOT_MET · 3 PENDING_DATA · 2 PENDING_EVAL

**Primary country:** CHN

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | shanghai_lockdown_industrial_production_drop_2022q2 | NOT_MET | 0 (2022) [peak_to_trough_pct_decline] | `>25% MoM decline in Shanghai industrial production 2022-04 vs 2022-03` |  |
| 2 | retail_sales_negative_2022 | PENDING_EVAL | 1.49 (2022) [max_in_window] | `retail-sales YoY <=-7% at 2022 trough` | threshold expression unparseable by regex |
| 3 | manufacturing_pmi_sub50_persistent | PENDING_DATA |  | `>=6 months of 2022 with manufacturing PMI <50` | No usable vintage for: owid:china_manufacturing_pmi |
| 4 | youth_unemployment_spike_2023 | PENDING_DATA |  | `>=20% peak` | No usable vintage for: ilostat:UNE_2EAP_SEX_AGE_RT_NB |
| 5 | incomplete_v_recovery_2023 | PENDING_EVAL | 0 (2023) [pct_increase_from_baseline] | `actual 2023 full-year real GDP growth <5.5% (vs IMF 2019 pre-COVID forecast ~6.0%)` | threshold expression unparseable by regex |
| 6 | stringency_index_extreme_2022 | PENDING_DATA |  | `>=70 mean stringency 2022 (vs OECD ~30)` | No usable vintage for: owid:government_response_stringency_index |

## Claim

> China's dynamic-zero-COVID policy 2020-2022, peaking with the Shanghai April-2022 lockdown and Beijing/Wuhan late-2022 closures, produced sharper-than-counterfactual demand contraction — retail-sales YoY turning negative, manufacturing PMI sub-50, and youth unemployment spiking — and the December-2022 abrupt reopening produced an incomplete and short-lived recovery rather than the V-shaped rebound expected from pent-up demand and excess household savings.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 2 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/china_zero_covid_2022_2023_demand_collapse_recovery.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
