# Result card - bis_reer_depreciation_current_account_repair_panel_1964_2026

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

Large real exchange-rate depreciations predict current-account improvement over the following three years.

## What Was Measured

- Outcome: `fwd_current_account_change_3y`.
- Treatment: `large_reer_depreciation`.
- Controls: `current_account_balance_gdp`.

## Results

- Usable panel: **7,584 observations**, **42 countries**.
- Coefficient on treatment: **-0.0385** (SE 0.4917, p=0.9376).
- Raw treated-control mean difference: **-0.2828**.
- Treated observations: **591**.

## Specification

`fwd_current_account_change_3y ~ large_reer_depreciation + reer_appreciation_12q + current_account_balance_gdp + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
