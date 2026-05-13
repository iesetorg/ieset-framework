# Result card - oecd_activation_spending_low_education_unemployment

**Verdict:** REFUTED - neither the regression nor raw high-low contrast gate clears.

## Plain-English Claim

Active labour-market programme spending is associated with lower low-education unemployment.

## Results

- Usable panel: **1,290 observations**, **36 country units**.
- Treatment: `socx_active_gdp`.
- Outcome: `low_education_unemployment`.
- Coefficient: **0.3667** (clustered SE 0.9656, p=0.7041).
- Top-quartile raw contrast: **-0.1679**.

## Specification

`low_education_unemployment ~ socx_active_gdp + epl + gdp_growth + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
