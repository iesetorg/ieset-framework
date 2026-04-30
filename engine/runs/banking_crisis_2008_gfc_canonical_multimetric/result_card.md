# Result card — banking_crisis_2008_gfc_canonical_multimetric

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 7 pending; 5 more need resolution

Pre-registered rule: SUPPORT if >= 5 of 7 metrics met; REFUTE if <= 2 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 1 PENDING_DATA · 6 PENDING_EVAL

**Primary country:** USA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | peak_to_trough_real_gdp_decline | PENDING_EVAL | 10.5 (2009) [peak_to_trough_pct_decline] | `decline >= 4% in at least 5 of 9 countries` | threshold expression unparseable by regex |
| 2 | unemployment_rate_peak_above_baseline | PENDING_EVAL | 66.5 (2010) [pct_increase_from_baseline] | `rise >= 5 pp in at least 5 of 9 countries` | threshold expression unparseable by regex |
| 3 | real_house_price_peak_to_trough | PENDING_EVAL |  | `decline >= 25% in at least 4 of 9 countries` | Non-tidy (needs custom parser): bis:WS_SPP |
| 4 | gross_government_debt_run_up | PENDING_EVAL | 61.8 (2013) [pct_increase_from_baseline] | `rise >= 25 pp of GDP in at least 5 of 9 countries` | threshold expression unparseable by regex |
| 5 | current_account_swing | PENDING_EVAL | -2.02 [max_loaded_value] | `swing >= 5 pp of GDP in at least 4 of 9 countries` | count-based threshold requires event log; data not sufficient to auto-count |
| 6 | bank_credit_to_gdp_decline | PENDING_EVAL | 6.94 (2011) [peak_to_trough_pct_decline] | `decline >= 15 pp in at least 4 of 9 countries` | threshold expression unparseable by regex |
| 7 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded in at least 7 of 9 countries` | No usable vintage for: owid:systemic-banking-crises |

## Claim

> The 2007-2009 Global Financial Crisis was a systemic banking-and-credit rupture in the advanced-economy core (USA, UK, Ireland, Iceland, Spain, the Eurozone periphery) with the canonical multi-metric pattern of large credit-to-GDP run-up followed by sharp output contraction, persistent unemployment, large fiscal-deficit blowout, and long real-house-price retracement. The hypothesis is that the GFC meets the canonical-case multi-metric checklist for a systemic banking crisis: at least 5 of the 7 pre-registered metrics breach their thresholds in 2007-2014.

## Interpretation

Verdict is **inconclusive (data gaps)** — 1 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 6 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_2008_gfc_canonical_multimetric.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
