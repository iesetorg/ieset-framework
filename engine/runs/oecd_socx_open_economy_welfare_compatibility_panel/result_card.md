# Result card - oecd_socx_open_economy_welfare_compatibility_panel

**Verdict:** PARTIAL - one of the regression or raw high-low contrast gates clears.

## Plain-English Claim

Open economies are more compatible with large public welfare states: social-spending employment penalties are smaller where trade exposure is high.

## Results

- Usable panel: **2,118 observations**, **42 country units**.
- Treatment: `socx_x_trade_open`.
- Outcome: `employment_rate`.
- Coefficient: **0.0021** (clustered SE 0.0010, p=0.0318).
- Top-quartile raw contrast: **-0.2682**.

## Specification

`employment_rate ~ socx_x_trade_open + socx_public_gdp + trade_open_gdp + gdp_growth + C(country) + C(year)`

This is a fixed-effects readiness screen using local vintages. It is not a standalone causal estimate.
