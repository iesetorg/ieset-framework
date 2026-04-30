# Result card — banking_crisis_cyprus_2013_bailin

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 2 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 1 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** CYP

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_decline | MET | 11.4 (2014) [peak_to_trough_pct_decline] | `>= 8% decline` |  |
| 2 | unemployment_rise | MET | 191 (2014) [pct_increase_from_baseline] | `>= 10 pp rise` |  |
| 3 | bank_credit_to_gdp_decline | NOT_MET | 46.9 (2018) [peak_to_trough_pct_decline] | `>= 100 pp of GDP decline` |  |
| 4 | esm_programme_2013 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:ESM_CYP_2013 |
| 5 | depositor_bailin_imposed | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:CYP_BAILIN_2013 |

## Claim

> The March 2013 Cyprus banking crisis, in which uninsured depositors at Bank of Cyprus and Laiki Bank were converted to equity / written down ("bail-in"), produced a real GDP peak-to-trough decline of >= 8%, a bank-credit-to-GDP decline of >= 100 pp, an unemployment-rate rise of >= 10 pp, and required an EUR 10bn ESM programme. The hypothesis is that the canonical multi-metric signature for Cyprus is met across at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_cyprus_2013_bailin.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
