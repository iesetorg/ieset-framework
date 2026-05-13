# Result card - cross_school_gov_consumption_child_mortality_social_provision_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher government-consumption shares predict lower child mortality.

## School Coverage

social_democratic, market_socialist

## What Was Measured

- Outcome: `child_mortality`.
- Treatment: `gov_consumption`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,235 observations**, **173 countries**.
- Coefficient on treatment: **-0.0131** (SE 0.1872, p=0.9441).

## Specification

`Q('child_mortality') ~ Q('gov_consumption') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
