# Result card - bis_credit_gap_current_account_twin_deficit_risk

**Verdict:** SUPPORTED - regression and raw contrast both clear the predeclared gates.

## Plain-English Claim

Credit-gap stress predicts larger unemployment increases when current accounts are in deficit.

## What Was Measured

- Outcome: `fwd_unemployment_change_2y`.
- Treatment: `credit_gap_x_current_account_deficit`.
- Controls: `credit_gap`, `current_account_balance_gdp`, `unemployment_rate`.

## Results

- Usable panel: **9,086 observations**, **42 countries**.
- Coefficient on treatment: **0.5958** (SE 0.2813, p=0.0342).
- Raw treated-control mean difference: **1.4465**.
- Treated observations: **1,081**.

## Specification

`fwd_unemployment_change_2y ~ credit_gap_x_current_account_deficit + credit_gap + current_account_balance_gdp + unemployment_rate + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
