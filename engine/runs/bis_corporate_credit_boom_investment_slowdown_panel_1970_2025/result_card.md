# Result card - bis_corporate_credit_boom_investment_slowdown_panel_1970_2025

**Verdict:** INCONCLUSIVE_DATA_PENDING - insufficient coverage for the predeclared gate.

## Plain-English Claim

Rapid private credit expansion predicts weaker private-investment share over the following five years.

## What Was Measured

- Outcome: `fwd_private_investment_share_change_5y`.
- Treatment: `credit_gdp_growth_5y`.
- Controls: `private_investment_share`, `gdp_growth`.

## Results

- Usable panel: **2,607 observations**, **14 countries**.
- Coefficient on treatment: **-0.0068** (SE 0.0156, p=0.6642).
- Raw treated-control mean difference: **-2.5683**.
- Treated observations: **6**.

## Specification

`fwd_private_investment_share_change_5y ~ credit_gdp_growth_5y + credit_gdp + private_investment_share + gdp_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
