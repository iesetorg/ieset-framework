# Result card — banking_crisis_brazil_proer_1995_1997

**Verdict:** supported

**Reason:** 3 of 4 metrics met threshold (support threshold 3)

Pre-registered rule: SUPPORT if >= 3 of 4 metrics met; REFUTE if <= 1 met (impossible to hit support).

**Counts:** 3 MET · 0 NOT_MET · 0 PENDING_DATA · 1 PENDING_EVAL

**Primary country:** BRA

## Metric-by-metric

| # | Metric | Status | Observed | Threshold | Notes |
|---|---|:---:|---:|---|---|
| 1 | proer_facility_creation_1995 | MET | 1 (1995) [yes_no_indicator_max] | `yes/no — yes counts as breach` | yes/no event evaluated from binary event indicator |
| 2 | bank_interventions_1995_1997 | MET | 3 (1997) [event_count_indicator_max] | `all three interventions executed by 1997` | all-three event threshold evaluated from coded count |
| 3 | laeven_valencia_systemic_banking_crisis | MET | 1 (1995) [coded_yes_indicator_max] | `coded yes (recognising PROER episode counts as systemic in LV)` | coded YES evaluated from binary event indicator |
| 4 | real_gdp_growth_undisturbed | PENDING_EVAL | 0 (1995) [pct_increase_from_baseline] | `annual growth >= 2% in each year (negative-control: PROER pre-empted macro spillover)` | threshold expression unparseable by regex |

## Claim

> Brazil's PROER (Programme to Stimulate the Restructuring and Strengthening of the National Financial System) of 1995-1997 — interventions in Banco Nacional, Banco Económico, Banco Bamerindus, central-bank liquidity facilities, and pre-emptive bank cleanup — is a canonical case of pre-emptive bank-balance-sheet cleanup in the wake of macro stabilisation (Plano Real 1994). The hypothesis is that PROER 1995-1997 meets a multi-metric checklist on at least 3 of 4 metrics, with the defining feature being preventive resolution prior to a Laeven-Valencia-coded systemic event.

## Interpretation

The canonical-case pattern match is satisfied: 3 of 4 pre-registered metrics meet their thresholds, above the support threshold of 3. Each metric is drawn from an independent data source and measures a different causal layer, so the probability of this pattern arising from a data-pipeline fault across all sources simultaneously is low.

## Steelman live concerns

See `hypotheses/steelman/banking_crisis_brazil_proer_1995_1997.md` for the strongest opposing arguments. Canonical-case multi-metric evidence is a pattern match, not a causal identification — the result card should be read as 'outcome trajectory matches the predicted pattern to degree X' rather than 'policy P caused the outcome'.

## Provenance

Vintages pinned in `manifest.yaml`. Full per-metric diagnostics in `diagnostics.json`. Machine-readable results in `metric_results.parquet`.
