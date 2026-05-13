# Result card - bis_dsr_house_price_boom_reversal_panel_1999_2025

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

House-price booms reverse more sharply when household debt-service burdens are high.

## What Was Measured

- Outcome: `fwd_real_house_price_growth_12q`.
- Treatment: `high_dsr_x_house_price_boom`.
- Controls: `lag_real_house_price_growth_8q`.

## Results

- Usable panel: **2,423 observations**, **17 countries**.
- Coefficient on treatment: **43.5886** (SE 25.5892, p=0.0885).
- Raw treated-control mean difference: **12.9030**.
- Treated observations: **17**.

## Specification

`fwd_real_house_price_growth_12q ~ high_dsr_x_house_price_boom + household_dsr + lag_real_house_price_growth_8q + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
