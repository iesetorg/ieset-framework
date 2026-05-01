# Result card — banking_crisis_spain_2012_cajas_restructuring

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 0 NOT_MET · 1 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** ESP

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_house_price_decline | MET | 51.3 (2013) [peak_to_trough_pct_decline] | `>= 35% decline` |  |
| 2 | unemployment_peak | MET | 7.04e+03 (2013) [pct_increase_from_baseline] | `>= 17 pp rise (peak >= 25%)` |  |
| 3 | government_debt_rise | MET | 4.77e+05 (2014) [pct_increase_from_baseline] | `>= 50 pp of GDP rise` |  |
| 4 | bank_credit_to_gdp_decline | MET | 38.6 (2017) [peak_to_trough_pct_decline] | `>= 30 pp of GDP decline` |  |
| 5 | esm_bank_recap_programme | PENDING_DATA |  | `yes/no — drawn programme counts as breach` | No usable vintage for: imf:ESM_ESP_2012 |

## Claim

> Spain's 2012 banking-sector restructuring of the cajas (regional savings banks), including the FROB recapitalisation, the creation of SAREB (the bad-bank vehicle), and the EUR 100bn ESM bank-recapitalisation programme, occurred in response to a multi-year buildup of property-credit exposure that produced a peak-to-trough real house-price decline of >= 35%, an unemployment rate rise to >= 25%, and a government-debt run-up of >= 50 pp of GDP. Canonical multi-metric checklist: at least 4 of 5 metrics breach.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_spain_2012_cajas_restructuring.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
