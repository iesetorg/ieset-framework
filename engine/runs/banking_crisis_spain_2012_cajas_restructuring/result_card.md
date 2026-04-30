# Result card — banking_crisis_spain_2012_cajas_restructuring

**Verdict:** inconclusive (data gaps)

**Reason:** 3 metrics met, 2 pending; 1 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 3 MET · 0 NOT_MET · 1 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** ESP

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_house_price_decline | PENDING_EVAL |  | `>= 35% decline` | Non-tidy (needs custom parser): bis:WS_SPP |
| 2 | unemployment_peak | MET | 132 (2013) [pct_increase_from_baseline] | `>= 17 pp rise (peak >= 25%)` |  |
| 3 | government_debt_rise | MET | 192 (2014) [pct_increase_from_baseline] | `>= 50 pp of GDP rise` |  |
| 4 | bank_credit_to_gdp_decline | MET | 38.6 (2017) [peak_to_trough_pct_decline] | `>= 30 pp of GDP decline` |  |
| 5 | esm_bank_recap_programme | PENDING_DATA |  | `yes/no — drawn programme counts as breach` | No usable vintage for: imf:ESM_ESP_2012 |

## Claim

> Spain's 2012 banking-sector restructuring of the cajas (regional savings banks), including the FROB recapitalisation, the creation of SAREB (the bad-bank vehicle), and the EUR 100bn ESM bank-recapitalisation programme, occurred in response to a multi-year buildup of property-credit exposure that produced a peak-to-trough real house-price decline of >= 35%, an unemployment rate rise to >= 25%, and a government-debt run-up of >= 50 pp of GDP. Canonical multi-metric checklist: at least 4 of 5 metrics breach.

## Interpretation

Verdict is **inconclusive (data gaps)** — 1 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_spain_2012_cajas_restructuring.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
