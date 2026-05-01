# Result card — banking_crisis_cyprus_2013_bailin

**Verdict:** supported

**Reason:** 4 of 5 metrics met threshold (support threshold 4)

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 4 MET · 1 NOT_MET · 0 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** CYP

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_decline | MET | 11.4 (2014) [peak_to_trough_pct_decline] | `>= 8% decline` |  |
| 2 | unemployment_rise | MET | 251 (2014) [pct_increase_from_baseline] | `>= 10 pp rise` |  |
| 3 | bank_credit_to_gdp_decline | NOT_MET | 46.9 (2018) [peak_to_trough_pct_decline] | `>= 100 pp of GDP decline` |  |
| 4 | esm_programme_2013 | MET | 1 (2013) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 5 | depositor_bailin_imposed | MET | 1 (2013) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |

## Claim

> The March 2013 Cyprus banking crisis, in which uninsured depositors at Bank of Cyprus and Laiki Bank were converted to equity / written down ("bail-in"), produced a real GDP peak-to-trough decline of >= 8%, a bank-credit-to-GDP decline of >= 100 pp, an unemployment-rate rise of >= 10 pp, and required an EUR 10bn ESM programme. The hypothesis is that the canonical multi-metric signature for Cyprus is met across at least 4 of 5 metrics.

## Interpretation

The canonical-case pattern match is satisfied: 4 of 5 pre-registered metrics meet their thresholds, above the support threshold of 4. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_cyprus_2013_bailin.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
