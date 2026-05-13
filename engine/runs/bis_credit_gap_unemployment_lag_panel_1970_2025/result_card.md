# Result card - bis_credit_gap_unemployment_lag_panel_1970_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

High BIS credit-gap episodes predict unemployment increases over the following two years.

## What Was Measured

- Outcome: `fwd_unemployment_change_2y`.
- Treatment: `high_credit_gap`.
- Controls: `unemployment_rate`.

## Results

- Usable panel: **9,573 observations**, **42 countries**.
- Coefficient on treatment: **0.2541** (SE 0.1659, p=0.1256).
- Raw treated-control mean difference: **0.9179**.
- Treated observations: **2,056**.

## Specification

`fwd_unemployment_change_2y ~ high_credit_gap + credit_gap + unemployment_rate + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
