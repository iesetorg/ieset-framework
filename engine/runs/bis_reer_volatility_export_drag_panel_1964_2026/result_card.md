# Result card - bis_reer_volatility_export_drag_panel_1964_2026

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

High real exchange-rate volatility predicts weaker export growth.

## What Was Measured

- Outcome: `fwd_export_growth_2y_avg`.
- Treatment: `high_reer_volatility`.
- Controls: `export_growth`.

## Results

- Usable panel: **7,920 observations**, **41 countries**.
- Coefficient on treatment: **-0.3038** (SE 0.2720, p=0.2641).
- Raw treated-control mean difference: **0.9675**.
- Treated observations: **2,095**.

## Specification

`fwd_export_growth_2y_avg ~ high_reer_volatility + reer_volatility_12q + export_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
