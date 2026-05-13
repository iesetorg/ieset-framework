# Result card - bls_qcew_county_food_service_minimum_wage_growth

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

County food-service employment grows more slowly when the state minimum wage rises faster.

## Results

- Usable panel: **25,228 observations**, **2,951 unit units**.
- Treatment: `min_wage_growth`.
- Outcome: `food_emp_growth`.
- Coefficient: **0.0389** (clustered SE 0.0162, p=0.0165).
- Top-quartile raw contrast: **1.7917**.

## Specification

`food_emp_growth ~ min_wage_growth + total_emp_growth + C(unit) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
