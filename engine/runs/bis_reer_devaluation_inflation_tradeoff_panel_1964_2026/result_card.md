# Result card - bis_reer_devaluation_inflation_tradeoff_panel_1964_2026

**Verdict:** PARTIAL - one of the regression or raw-contrast gates clears, but not both.

## Plain-English Claim

Large real exchange-rate depreciations are followed by higher inflation over the next two years.

## What Was Measured

- Outcome: `fwd_inflation_2y_avg`.
- Treatment: `large_reer_depreciation`.
- Controls: `inflation`.

## Results

- Usable panel: **8,120 observations**, **42 countries**.
- Coefficient on treatment: **1.1999** (SE 0.9229, p=0.1935).
- Raw treated-control mean difference: **3.1901**.
- Treated observations: **615**.

## Specification

`fwd_inflation_2y_avg ~ large_reer_depreciation + reer_appreciation_12q + inflation + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
