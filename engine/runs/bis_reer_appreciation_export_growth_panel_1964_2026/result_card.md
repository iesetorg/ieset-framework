# Result card - bis_reer_appreciation_export_growth_panel_1964_2026

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

Large real exchange-rate appreciations predict weaker export growth over the following two years.

## What Was Measured

- Outcome: `fwd_export_growth_2y_avg`.
- Treatment: `large_reer_appreciation`.
- Controls: `export_growth`.

## Results

- Usable panel: **7,920 observations**, **41 countries**.
- Coefficient on treatment: **0.2720** (SE 0.6334, p=0.6677).
- Raw treated-control mean difference: **0.5861**.
- Treated observations: **530**.

## Specification

`fwd_export_growth_2y_avg ~ large_reer_appreciation + reer_appreciation_12q + export_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
