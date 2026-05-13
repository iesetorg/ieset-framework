# Result card - bis_credit_gap_property_price_interaction_panel_1970_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Credit gaps are more damaging when they coincide with real house-price booms.

## What Was Measured

- Outcome: `fwd_real_house_price_growth_12q`.
- Treatment: `credit_gap_x_house_price_boom`.
- Controls: `lag_real_house_price_growth_8q`.

## Results

- Usable panel: **8,038 observations**, **41 countries**.
- Coefficient on treatment: **-1.5356** (SE 5.8464, p=0.7928).
- Raw treated-control mean difference: **-20.3258**.
- Treated observations: **310**.

## Specification

`fwd_real_house_price_growth_12q ~ credit_gap_x_house_price_boom + credit_gap + lag_real_house_price_growth_8q + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
