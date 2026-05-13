# Result card - bis_credit_gap_manufacturing_share_drag_panel_1970_2025

**Verdict:** REFUTED - neither the regression nor raw-contrast gate clears.

## Plain-English Claim

High credit-gap episodes predict later manufacturing-share erosion.

## What Was Measured

- Outcome: `fwd_manufacturing_share_change_3y`.
- Treatment: `high_credit_gap`.
- Controls: `manufacturing_share`.

## Results

- Usable panel: **9,864 observations**, **42 countries**.
- Coefficient on treatment: **0.1360** (SE 0.1486, p=0.3601).
- Raw treated-control mean difference: **0.0259**.
- Treated observations: **2,167**.

## Specification

`fwd_manufacturing_share_change_3y ~ high_credit_gap + credit_gap + manufacturing_share + C(country) + C(year)`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
