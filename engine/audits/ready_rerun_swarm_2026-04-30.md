# READY Rerun Swarm - 2026-04-30

## Summary

- Spawned three read-only sidecars to triage spec-sharpening, data/source, and runner/parser blockers.
- Patched `scripts/run_multi_metric_checklist.py` to reuse the stronger panel normalizer, avoid misclassifying plain numeric thresholds as event counts, avoid treating every `ratio` mention as cross-country, and persist stub-refusal diagnostics.
- Patched `scripts/run_panel_fe.py` to block interaction-required specs when no loadable constructed interaction term is defined, preventing false main-effect grading.
- Reran 33 READY multi-metric inconclusive/missing cases.
- Reran 47 preflight-ready non-checklist inconclusive cases through the repo rerun script.

## Decisive Movement

- Banking-crisis canonical checklist batch moved from `23/23 INCONCLUSIVE_PENDING_DATA` to `3 SUPPORTED`, `1 REFUTED`, and `19 INCONCLUSIVE_PENDING_DATA`.
- Banking metric resolution moved from prior `26 MET / 9 NOT_MET / 49 PENDING_DATA / 31 PENDING_EVAL` to current `44 MET / 10 NOT_MET / 46 PENDING_DATA / 15 PENDING_EVAL`.
- The 47 broader preflight-ready reruns did not produce decisive verdicts; they persisted concrete blockers: insufficient observations, insufficient pre/post windows, insufficient donor coverage, or interaction-not-constructible.

## Current Banking Verdicts

| verdict | count |
| --- | ---: |
| `INCONCLUSIVE_PENDING_DATA` | 19 |
| `SUPPORTED` | 3 |
| `REFUTED` | 1 |

## Current Banking Rows

| hypothesis_id | verdict | MET | NOT_MET | PENDING_DATA | PENDING_EVAL | total |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `banking_crisis_2008_gfc_canonical_multimetric` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 1 | 6 | 7 |
| `banking_crisis_argentina_2001_corralito_canonical` | `INCONCLUSIVE_PENDING_DATA` | 3 | 1 | 2 | 0 | 6 |
| `banking_crisis_asian_financial_crisis_1997_panel` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 2 | 1 | 5 |
| `banking_crisis_brazil_1999_real_devaluation` | `SUPPORTED` | 3 | 0 | 1 | 0 | 4 |
| `banking_crisis_brazil_proer_1995_1997` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 1 | 4 |
| `banking_crisis_china_2015_2020_panel` | `INCONCLUSIVE_PENDING_DATA` | 1 | 1 | 2 | 0 | 4 |
| `banking_crisis_cyprus_2013_bailin` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 2 | 0 | 5 |
| `banking_crisis_greece_2010_2018_doom_loop` | `INCONCLUSIVE_PENDING_DATA` | 4 | 0 | 2 | 0 | 6 |
| `banking_crisis_iceland_2008_canonical_multimetric` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 1 | 2 | 6 |
| `banking_crisis_ireland_2008_property_bust` | `SUPPORTED` | 4 | 0 | 1 | 0 | 5 |
| `banking_crisis_italy_2016_2017_mps` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 2 | 0 | 4 |
| `banking_crisis_japan_1990_lost_decade` | `INCONCLUSIVE_PENDING_DATA` | 1 | 1 | 3 | 0 | 5 |
| `banking_crisis_latvia_2008_parex` | `INCONCLUSIVE_PENDING_DATA` | 3 | 0 | 2 | 0 | 5 |
| `banking_crisis_lebanon_2019_2024_collapse` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 3 | 0 | 6 |
| `banking_crisis_mexico_tequila_1994_canonical` | `REFUTED` | 1 | 2 | 2 | 0 | 5 |
| `banking_crisis_nordic_1991_1993_panel` | `INCONCLUSIVE_PENDING_DATA` | 2 | 0 | 3 | 0 | 5 |
| `banking_crisis_russia_1998_default_canonical` | `INCONCLUSIVE_PENDING_DATA` | 3 | 0 | 2 | 0 | 5 |
| `banking_crisis_south_africa_african_bank_2014` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 3 | 1 | 4 |
| `banking_crisis_spain_2012_cajas_restructuring` | `SUPPORTED` | 4 | 0 | 1 | 0 | 5 |
| `banking_crisis_turkey_2001_canonical` | `INCONCLUSIVE_PENDING_DATA` | 2 | 1 | 2 | 0 | 5 |
| `banking_crisis_us_2023_svb_signature` | `INCONCLUSIVE_PENDING_DATA` | 0 | 0 | 2 | 3 | 5 |
| `banking_crisis_us_sl_crisis_1986_1995` | `INCONCLUSIVE_PENDING_DATA` | 3 | 0 | 2 | 0 | 5 |
| `banking_crisis_vietnam_2012_2015_restructuring` | `INCONCLUSIVE_PENDING_DATA` | 0 | 1 | 2 | 1 | 4 |

## Current READY Multi-Metric Summary

| verdict | count |
| --- | ---: |
| `INCONCLUSIVE_PENDING_DATA` | 24 |
| `INCONCLUSIVE_DATA_PENDING` | 5 |
| `SUPPORTED` | 4 |
| `REFUTED` | 2 |
| `supported_subset — stagnation confirmed (mean growth 0.96%); ≤1 of 4 canonical wellbeing indicators degraded. Cantril ladder NOT on disk; canonical basket coverage 6/7 (Gallup WHR fetcher not landed). NOT graded SUPPORTED because the canonical basket is incomplete.` | 1 |

## Next Highest Levers

- Add/alias `owid:systemic-banking-crises` or a Laeven-Valencia event vintage; this remains the biggest banking-crisis data unlock.
- Add manual event vintages for IMF-style crisis events (`*_DEFAULT_*`, `*_BAILIN_*`, `*_SBA_*`, `*_ESM_*`, bank intervention events).
- Add explicit constructed interaction variables or bespoke replication scripts for interaction-required panel specs now blocked by the integrity guard.
- For the 47 broader reruns, the next move is not rerun volume; it is respecification/frequency changes for insufficient-observation and insufficient-pre-period designs.
