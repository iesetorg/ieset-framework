# Result card - bis_reer_appreciation_industrial_share_panel_1964_2026

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Large real exchange-rate appreciations predict later erosion in manufacturing value-added share.

## What Was Measured

- Outcome: `fwd_manufacturing_share_change_3y`.
- Treatment: `large_reer_appreciation`.
- Controls: `manufacturing_share`.

## Results

- Usable panel: **7,648 observations**, **42 countries**.
- Coefficient on treatment: **0.1108** (SE 0.2366, p=0.6395).
- Raw treated-control mean difference: **-0.6838**.
- Treated observations: **532**.

## Specification

`fwd_manufacturing_share_change_3y ~ large_reer_appreciation + reer_appreciation_12q + manufacturing_share + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
