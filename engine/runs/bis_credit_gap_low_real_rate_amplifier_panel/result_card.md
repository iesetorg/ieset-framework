# Result card - bis_credit_gap_low_real_rate_amplifier_panel

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Credit-gap stress is more dangerous when real interest rates are unusually low.

## What Was Measured

- Outcome: `fwd_unemployment_change_2y`.
- Treatment: `credit_gap_x_low_real_rate`.
- Controls: `credit_gap`, `real_interest_rate`, `unemployment_rate`.

## Results

- Usable panel: **5,282 observations**, **28 countries**.
- Coefficient on treatment: **0.2207** (SE 0.2333, p=0.3442).
- Raw treated-control mean difference: **0.2647**.
- Treated observations: **223**.

## Specification

`fwd_unemployment_change_2y ~ credit_gap_x_low_real_rate + credit_gap + real_interest_rate + unemployment_rate + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
