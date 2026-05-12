# Result card - cross_school_tax_revenue_poverty_reduction_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Higher tax revenue shares predict lower extreme poverty.

## School Coverage

social_democratic, market_socialist

## What Was Measured

- Outcome: `poverty`.
- Treatment: `tax_revenue`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,728 observations**, **139 countries**.
- Coefficient on treatment: **-0.3955** (SE 0.1082, p=0.0003).

## Specification

`Q('poverty') ~ Q('tax_revenue') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
