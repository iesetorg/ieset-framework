# Result card - bis_corporate_dsr_investment_slowdown_panel_1999_2025

**Verdict:** INCONCLUSIVE_DATA_PENDING - insufficient coverage for the predeclared gate.

## Plain-English Claim

High non-financial corporate debt-service burdens predict later private-investment-share declines.

## What Was Measured

- Outcome: `fwd_private_investment_share_change_3y`.
- Treatment: `high_corporate_dsr`.
- Controls: `corporate_dsr`, `private_investment_share`, `gdp_growth`.

## Results

- Usable panel: **364 observations**, **2 countries**.
- Coefficient on treatment: **-0.9112** (SE 0.2967, p=0.0021).
- Raw treated-control mean difference: **-0.8866**.
- Treated observations: **98**.

## Specification

`fwd_private_investment_share_change_3y ~ high_corporate_dsr + corporate_dsr + private_investment_share + gdp_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
