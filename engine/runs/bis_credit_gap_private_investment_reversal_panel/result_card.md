# Result card - bis_credit_gap_private_investment_reversal_panel

**Verdict:** INCONCLUSIVE_DATA_PENDING - insufficient coverage for the predeclared gate.

## Plain-English Claim

High BIS credit-gap episodes predict weaker private-investment share over the following three years.

## What Was Measured

- Outcome: `fwd_private_investment_share_change_3y`.
- Treatment: `high_credit_gap`.
- Controls: `credit_gap`, `private_investment_share`, `gdp_growth`.

## Results

- Usable panel: **3,147 observations**, **14 countries**.
- Coefficient on treatment: **-1.5527** (SE 0.5851, p=0.0080).
- Raw treated-control mean difference: **-2.5438**.
- Treated observations: **626**.

## Specification

`fwd_private_investment_share_change_3y ~ high_credit_gap + credit_gap + private_investment_share + gdp_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
