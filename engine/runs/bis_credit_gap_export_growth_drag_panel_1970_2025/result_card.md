# Result card - bis_credit_gap_export_growth_drag_panel_1970_2025

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

High credit-gap episodes predict weaker export growth as domestic credit booms unwind.

## What Was Measured

- Outcome: `fwd_export_growth_2y_avg`.
- Treatment: `high_credit_gap`.
- Controls: `export_growth`.

## Results

- Usable panel: **12,155 observations**, **41 countries**.
- Coefficient on treatment: **-0.1377** (SE 0.3110, p=0.6579).
- Raw treated-control mean difference: **-0.6261**.
- Treated observations: **2,346**.

## Specification

`fwd_export_growth_2y_avg ~ high_credit_gap + credit_gap + export_growth + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
