# Result card - bis_reer_appreciation_inflation_relief_panel_1964_2026

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

Large real exchange-rate appreciations predict lower inflation over the following two years.

## What Was Measured

- Outcome: `fwd_inflation_2y_avg`.
- Treatment: `large_reer_appreciation`.
- Controls: `inflation`.

## Results

- Usable panel: **8,120 observations**, **42 countries**.
- Coefficient on treatment: **0.1073** (SE 0.4921, p=0.8273).
- Raw treated-control mean difference: **2.8494**.
- Treated observations: **564**.

## Specification

`fwd_inflation_2y_avg ~ large_reer_appreciation + reer_appreciation_12q + inflation + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
