# Result card - cross_school_fiscal_balance_growth_austerity_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Stronger fiscal balances predict slower GDP growth if consolidation is contractionary.

## School Coverage

post_keynesian, social_democratic

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `fiscal_balance`.
- Controls: none.

## Results

- Usable panel: **3,609 observations**, **157 countries**.
- Coefficient on treatment: **0.0543** (SE 0.0369, p=0.1415).

## Specification

`Q('gdp_pc_growth') ~ Q('fiscal_balance') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
