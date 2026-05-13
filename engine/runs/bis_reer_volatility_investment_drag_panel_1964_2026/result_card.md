# Result card - bis_reer_volatility_investment_drag_panel_1964_2026

**Verdict:** INCONCLUSIVE_DATA_PENDING - insufficient coverage for the predeclared gate.

## Plain-English Claim

Higher real exchange-rate volatility predicts lower private-investment share.

## What Was Measured

- Outcome: `fwd_private_investment_share_change_3y`.
- Treatment: `high_reer_volatility`.
- Controls: `private_investment_share`, `gdp_growth`.

## Results

- Usable panel: **2,349 observations**, **14 countries**.
- Coefficient on treatment: **0.1886** (SE 0.2852, p=0.5084).
- Raw treated-control mean difference: **0.0394**.
- Treated observations: **670**.

## Specification

`fwd_private_investment_share_change_3y ~ high_reer_volatility + reer_volatility_12q + private_investment_share + gdp_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
