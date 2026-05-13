# Result card - oecd_low_education_unemployment_minimum_wage_bite

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

Higher OECD statutory minimum-wage bite ratios are associated with higher low-education unemployment.

## Results

- Usable panel: **1,094 observations**, **28 country units**.
- Treatment: `minimum_wage_bite`.
- Outcome: `low_education_unemployment`.
- Coefficient: **-0.9799** (clustered SE 3.8102, p=0.7970).
- Top-quartile raw contrast: **-2.6181**.

## Specification

`low_education_unemployment ~ minimum_wage_bite + epl + gdp_growth + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
