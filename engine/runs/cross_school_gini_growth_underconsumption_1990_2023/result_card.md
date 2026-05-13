# Result card - cross_school_gini_growth_underconsumption_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher inequality predicts slower GDP per-capita growth.

## School Coverage

marxian, social_democratic

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `gini`.
- Controls: none.

## Results

- Usable panel: **2,205 observations**, **171 countries**.
- Coefficient on treatment: **-0.0257** (SE 0.0341, p=0.4515).

## Specification

`Q('gdp_pc_growth') ~ Q('gini') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
