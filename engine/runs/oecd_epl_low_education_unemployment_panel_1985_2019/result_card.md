# Result card - oecd_epl_low_education_unemployment_panel_1985_2019

**Verdict:** PARTIAL - one of the regression or raw high-low contrast gates clears.

## Plain-English Claim

Stricter OECD employment protection is associated with higher unemployment among below-upper-secondary adults.

## Results

- Usable panel: **1,301 observations**, **36 country units**.
- Treatment: `epl`.
- Outcome: `low_education_unemployment`.
- Coefficient: **0.8637** (clustered SE 1.1530, p=0.4538).
- Top-quartile raw contrast: **2.5316**.

## Specification

`low_education_unemployment ~ epl + gdp_growth + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
