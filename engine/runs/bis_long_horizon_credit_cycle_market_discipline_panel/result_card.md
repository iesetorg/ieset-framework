# Result card - bis_long_horizon_credit_cycle_market_discipline_panel

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Credit booms predict weaker five-year real GDP-per-capita growth, consistent with later market discipline.

## What Was Measured

- Outcome: `fwd_gdp_pc_growth_5y_avg`.
- Treatment: `high_credit_gap`.
- Controls: `credit_gap`, `gdp_pc_growth`.

## Results

- Usable panel: **11,433 observations**, **42 countries**.
- Coefficient on treatment: **-0.2408** (SE 0.1942, p=0.2150).
- Raw treated-control mean difference: **-0.6829**.
- Treated observations: **2,244**.

## Specification

`fwd_gdp_pc_growth_5y_avg ~ high_credit_gap + credit_gap + gdp_pc_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
