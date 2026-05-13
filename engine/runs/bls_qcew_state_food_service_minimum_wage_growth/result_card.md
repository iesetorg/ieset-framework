# Result card - bls_qcew_state_food_service_minimum_wage_growth

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

State food-service employment grows more slowly when the state minimum wage rises faster.

## Results

- Usable panel: **510 observations**, **51 unit units**.
- Treatment: `min_wage_growth`.
- Outcome: `food_emp_growth`.
- Coefficient: **0.0150** (clustered SE 0.0310, p=0.6293).
- Top-quartile raw contrast: **2.0491**.

## Specification

`food_emp_growth ~ min_wage_growth + total_emp_growth + C(unit) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
