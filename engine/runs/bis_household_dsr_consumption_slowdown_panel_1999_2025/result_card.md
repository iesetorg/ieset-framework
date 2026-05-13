# Result card - bis_household_dsr_consumption_slowdown_panel_1999_2025

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

High household debt-service burdens predict weaker private-consumption growth over the next two years.

## What Was Measured

- Outcome: `fwd_consumption_growth_2y_avg`.
- Treatment: `high_household_dsr`.
- Controls: `consumption_growth`.

## Results

- Usable panel: **3,094 observations**, **17 countries**.
- Coefficient on treatment: **0.1597** (SE 0.3584, p=0.6559).
- Raw treated-control mean difference: **-0.6656**.
- Treated observations: **262**.

## Specification

`fwd_consumption_growth_2y_avg ~ high_household_dsr + household_dsr + consumption_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
