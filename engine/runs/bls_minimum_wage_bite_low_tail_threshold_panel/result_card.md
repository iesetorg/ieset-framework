# Result card - bls_minimum_wage_bite_low_tail_threshold_panel

**Verdict:** SUPPORTED - regression and raw high-low contrast both clear the predeclared gates.

## Plain-English Claim

Very high minimum-wage bite ratios relative to the state low-wage tail predict weaker total employment growth.

## Results

- Usable panel: **408 observations**, **51 unit units**.
- Treatment: `high_low_tail_bite`.
- Outcome: `total_emp_growth`.
- Coefficient: **-0.2206** (clustered SE 0.1276, p=0.0840).
- Top-quartile raw contrast: **-0.3917**.

## Specification

`total_emp_growth ~ high_low_tail_bite + bite_ratio + C(unit) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
