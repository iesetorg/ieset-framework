# Result card — NZ Rogernomics 1984 productivity effect

**Verdict:** refuted — NZ synthetic-control log-TFP gap mean over 1995-2005 = -3.80% (<= 0); informative log GDP-pc gap = -22.70%. Productivity acceleration claim not supported by the data: NZ TFP sits at or below its synthetic counterfactual built from 8 donor advanced economies.

## Summary

- Treated unit: **NZL**, treatment year **1984** (Lange-Douglas reforms).
- Donor pool: AUS, IRL, FIN, DNK, SWE, NOR, GBR, CAN.
- Outcome (PRIMARY, dispositive): log TFP (PWT rtfpna).
- Outcome (INFORMATIVE, non-gating): log real GDP per capita (PWT rgdpna / pop).
- Post-treatment evaluation window: 1995-2005.

## PRIMARY result

- Mean synthetic-control gap on log TFP, 1995-2005: **-3.80%** (SUPPORTED threshold: ≥ +5%; REFUTED threshold: ≤ 0%).
- Pre-treatment fit RMSE on log TFP: **0.0497** (method-valid gate: ≤ 0.05).
- Donors with full 1970-2005 coverage: **8** (method-valid gate: ≥ 4).
- Donor weights: AUS=0.36, IRL=0.00, FIN=0.00, DNK=0.00, SWE=0.00, NOR=0.00, GBR=0.00, CAN=0.64.

## INFORMATIVE result (real-income channel)

- Mean synthetic-control gap on log real GDP per capita, 1995-2005: **-22.70%** (does not gate the verdict).

## Method

Classic Abadie-Diamond-Hainmueller (2010) synthetic-control estimator, donor weights chosen by SLSQP over the unit simplex to minimise pre-treatment squared loss. The spec calls for synth_did; the simpler ADH estimator is what the framework currently implements consistently across runs (see `engine/runs/estonia_market_reform_post_soviet_growth_1991_2007/`).

Method-validity gates (per HYPOTHESIS_FRAMEWORK_AUDIT.md §E2): pre-fit RMSE ≤ 0.05 and donor coverage ≥ 4. A failure on either gate emits `inconclusive`, never `refuted`.

## Data

- pwt:rtfpna (TFP at constant national prices)
- pwt:rgdpna (real GDP at constant national prices)
- pwt:pop (population)

Vintages pinned in `manifest.yaml`. Reproduce with `python3 replication.py`.
