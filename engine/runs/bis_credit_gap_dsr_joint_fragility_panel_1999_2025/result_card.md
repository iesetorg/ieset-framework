# Result card - bis_credit_gap_dsr_joint_fragility_panel_1999_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Credit-gap stress is more damaging when household debt-service burdens are also high.

## What Was Measured

- Outcome: `fwd_unemployment_change_2y`.
- Treatment: `credit_gap_x_high_dsr`.
- Controls: `credit_gap`, `household_dsr`, `unemployment_rate`.

## Results

- Usable panel: **3,366 observations**, **17 countries**.
- Coefficient on treatment: **-1.1245** (SE 0.6652, p=0.0909).
- Raw treated-control mean difference: **0.9497**.
- Treated observations: **112**.

## Specification

`fwd_unemployment_change_2y ~ credit_gap_x_high_dsr + credit_gap + household_dsr + unemployment_rate + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
