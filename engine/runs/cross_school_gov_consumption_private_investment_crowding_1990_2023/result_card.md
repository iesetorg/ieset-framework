# Result card - cross_school_gov_consumption_private_investment_crowding_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Higher government consumption predicts lower private investment if crowding out dominates.

## School Coverage

post_keynesian, austrian

## What Was Measured

- Outcome: `private_investment`.
- Treatment: `gov_consumption`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,152 observations**, **99 countries**.
- Coefficient on treatment: **0.0101** (SE 0.0486, p=0.8360).

## Specification

`Q('private_investment') ~ Q('gov_consumption') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
