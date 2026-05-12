# Result card - cross_school_tax_revenue_gini_redistribution_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Higher tax revenue shares predict lower inequality.

## School Coverage

social_democratic, market_socialist

## What Was Measured

- Outcome: `gini`.
- Treatment: `tax_revenue`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,728 observations**, **139 countries**.
- Coefficient on treatment: **-0.1087** (SE 0.0632, p=0.0854).

## Specification

`Q('gini') ~ Q('tax_revenue') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
