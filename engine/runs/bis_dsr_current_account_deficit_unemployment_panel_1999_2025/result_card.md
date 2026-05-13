# Result card - bis_dsr_current_account_deficit_unemployment_panel_1999_2025

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Household debt-service stress predicts larger unemployment increases when the current account is also in deficit.

## What Was Measured

- Outcome: `fwd_unemployment_change_2y`.
- Treatment: `high_dsr_x_current_account_deficit`.
- Controls: `current_account_balance_gdp`, `unemployment_rate`.

## Results

- Usable panel: **3,344 observations**, **17 countries**.
- Coefficient on treatment: **-0.2373** (SE 0.6049, p=0.6948).
- Raw treated-control mean difference: **1.1427**.
- Treated observations: **108**.

## Specification

`fwd_unemployment_change_2y ~ high_dsr_x_current_account_deficit + household_dsr + current_account_balance_gdp + unemployment_rate + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
