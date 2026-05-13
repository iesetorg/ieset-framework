# Result card - bis_credit_gap_house_price_reversal_oecd_1970_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Elevated BIS credit gaps predict weaker three-year real house-price growth.

## What Was Measured

- Outcome: `fwd_real_house_price_growth_12q`.
- Treatment: `high_credit_gap`.
- Controls: `credit_gap`, `lag_real_house_price_growth_8q`.

## Results

- Usable panel: **8,038 observations**, **41 countries**.
- Coefficient on treatment: **-6.1664** (SE 3.3000, p=0.0617).
- Raw treated-control mean difference: **-6.1269**.
- Treated observations: **1,476**.

## Specification

`fwd_real_house_price_growth_12q ~ high_credit_gap + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
