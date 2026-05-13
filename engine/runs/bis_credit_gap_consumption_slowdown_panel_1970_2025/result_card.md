# Result card - bis_credit_gap_consumption_slowdown_panel_1970_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

High BIS credit-gap episodes predict weaker private-consumption growth over the following two years.

## What Was Measured

- Outcome: `fwd_consumption_growth_2y_avg`.
- Treatment: `high_credit_gap`.
- Controls: `consumption_growth`.

## Results

- Usable panel: **12,109 observations**, **42 countries**.
- Coefficient on treatment: **-0.2235** (SE 0.1666, p=0.1798).
- Raw treated-control mean difference: **-0.6972**.
- Treated observations: **2,388**.

## Specification

`fwd_consumption_growth_2y_avg ~ high_credit_gap + credit_gap + consumption_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
