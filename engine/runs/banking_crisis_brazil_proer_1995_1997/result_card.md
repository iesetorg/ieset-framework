# Result card — banking_crisis_brazil_proer_1995_1997

**Verdict:** inconclusive (data gaps)

**Reason:** 0 metrics met, 4 pending; 3 more need resolution

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 0 MET · 0 NOT_MET · 3 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** BRA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | proer_facility_creation_1995 | PENDING_DATA |  | `yes/no — yes counts as breach` | No usable vintage for: imf:BRA_PROER_1995 |
| 2 | bank_interventions_1995_1997 | PENDING_DATA |  | `all three interventions executed by 1997` | No usable vintage for: imf:BRA_BANK_INTERVENTIONS_1995_1997 |
| 3 | laeven_valencia_systemic_banking_crisis | PENDING_DATA |  | `coded yes (recognising PROER episode counts as systemic in LV)` | No usable vintage for: owid:systemic-banking-crises |
| 4 | real_gdp_growth_undisturbed | PENDING_EVAL | 0 (1995) [pct_increase_from_baseline] | `annual growth >= 2% in each year (negative-control: PROER pre-empted macro spillover)` | threshold expression unparseable by regex |

## Claim

> Brazil's PROER (Programme to Stimulate the Restructuring and Strengthening of the National Financial System) of 1995-1997 — interventions in Banco Nacional, Banco Económico, Banco Bamerindus, central-bank liquidity facilities, and pre-emptive bank cleanup — is a canonical case of pre-emptive bank-balance-sheet cleanup in the wake of macro stabilisation (Plano Real 1994). The hypothesis is that PROER 1995-1997 meets a multi-metric checklist on at least 3 of 4 metrics, with the defining feature being preventive resolution prior to a Laeven-Valencia-coded systemic event.

## Interpretation

Verdict is **inconclusive (data gaps)** — 3 metric(s) cannot be evaluated because the underlying data source is not yet in the vintages pipeline, and 1 metric(s) have data but a threshold expression the auto-evaluator does not recognise (complex conditions, discrete event counts, cross-country gaps). Close these gaps then re-run.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_brazil_proer_1995_1997.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
