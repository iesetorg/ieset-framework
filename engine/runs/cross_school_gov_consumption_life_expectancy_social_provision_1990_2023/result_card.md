# Result card - cross_school_gov_consumption_life_expectancy_social_provision_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher government-consumption shares predict higher life expectancy.

## School Coverage

social_democratic, market_socialist

## What Was Measured

- Outcome: `life_expectancy`.
- Treatment: `gov_consumption`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,487 observations**, **185 countries**.
- Coefficient on treatment: **-0.0102** (SE 0.0185, p=0.5811).

## Specification

`Q('life_expectancy') ~ Q('gov_consumption') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
