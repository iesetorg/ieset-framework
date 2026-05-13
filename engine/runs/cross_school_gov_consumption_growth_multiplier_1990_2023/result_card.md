# Result card - cross_school_gov_consumption_growth_multiplier_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher government consumption predicts faster GDP per-capita growth.

## School Coverage

post_keynesian, new_keynesian

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `gov_consumption`.
- Controls: none.

## Results

- Usable panel: **5,487 observations**, **185 countries**.
- Coefficient on treatment: **-0.0909** (SE 0.0892, p=0.3085).

## Specification

`Q('gdp_pc_growth') ~ Q('gov_consumption') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
