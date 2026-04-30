# Result card — banking_crisis_russia_1998_default_canonical

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 3 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 0 NOT_MET · 3 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** RUS

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | ruble_depreciation_1998 | PENDING_DATA |  | `>= 60% depreciation` | No usable vintage for: imf:ENDA_XDC_USD_RATE; Non-tidy (needs custom parser): bis:WS_EER |
| 2 | real_gdp_decline | MET | 100 (1998) [peak_to_trough_pct_decline] | `>= 5% peak-to-trough decline` |  |
| 3 | sovereign_default_event | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:RUS_DEFAULT_1998 |
| 4 | systemic_banking_crisis_coded | PENDING_DATA |  | `coded yes` | No usable vintage for: owid:systemic-banking-crises |
| 5 | cpi_inflation_spike | MET | 210 (1999) [pct_increase_from_baseline] | `>= 50 pp YoY peak rise` |  |

## Claim

> The August 1998 Russian crisis — domestic-currency sovereign default, ruble devaluation of >= 60% against USD, real-GDP contraction of >= 5%, banking-system collapse with widespread bank failures, and IMF programme entry — is the canonical EM sovereign-and-banking-twin-default case of the late 1990s. The hypothesis is that Russia 1998 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_russia_1998_default_canonical.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
