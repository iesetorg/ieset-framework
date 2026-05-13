# Result card - bls_oews_median_bite_food_service_employment_panel

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

Higher state minimum-wage bite ratios relative to median wages are associated with weaker food-service employment growth.

## Results

- Usable panel: **408 observations**, **51 unit units**.
- Treatment: `bite_ratio`.
- Outcome: `food_emp_growth`.
- Coefficient: **1.5833** (clustered SE 1.9251, p=0.4108).
- Top-quartile raw contrast: **1.2163**.

## Specification

`food_emp_growth ~ bite_ratio + total_emp_growth + C(unit) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
