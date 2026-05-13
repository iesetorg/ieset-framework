# Result card - oecd_socx_public_social_spending_employment_tradeoff

**Verdict:** SUPPORTED - regression and raw high-low contrast both clear the predeclared gates.

## Plain-English Claim

Higher public social spending shares are associated with lower employment rates once country and year effects are absorbed.

## Results

- Usable panel: **2,127 observations**, **42 country units**.
- Treatment: `socx_public_gdp`.
- Outcome: `employment_rate`.
- Coefficient: **-0.3638** (clustered SE 0.0931, p=0.0001).
- Top-quartile raw contrast: **-3.1786**.

## Specification

`employment_rate ~ socx_public_gdp + gdp_growth + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
