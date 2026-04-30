# Result card — banking_crisis_latvia_2008_parex

**Verdict:** inconclusive (data gaps)

**Reason:** 2 metrics met, 2 pending; 2 more need resolution

Pre-registered rule: SUPPORT if >= 4 of 5 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 2 MET · 1 NOT_MET · 2 PENDING_DATA · 0 PENDING_EVAL

**Primary country:** LVA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | real_gdp_decline | NOT_MET | 19.1 (2010) [peak_to_trough_pct_decline] | `>= 20% decline` |  |
| 2 | unemployment_rise | MET | 152 (2010) [pct_increase_from_baseline] | `>= 13 pp rise` |  |
| 3 | imf_eu_programme | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:SBA_LVA_2008 |
| 4 | parex_nationalisation | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:LVA_PAREX_2008 |
| 5 | bank_credit_to_gdp_decline | MET | 44.9 (2014) [peak_to_trough_pct_decline] | `>= 30 pp of GDP decline` |  |

## Claim

> Latvia's 2008-2010 banking crisis — Parex Banka nationalisation in November 2008, EUR-peg defence, EUR 7.5bn IMF / EU programme, real-GDP cumulative decline of >= 20% peak-to-trough, and unemployment-rate rise of >= 13 pp — is a canonical small-open-economy hard-peg-defence + banking-rescue case from the GFC era. The hypothesis is that Latvia 2008-2010 meets the canonical multi-metric checklist on at least 4 of 5 metrics.

## Interpretation

Verdict is **inconclusive (data gaps)** — 2 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 0 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_latvia_2008_parex.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
