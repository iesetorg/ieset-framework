# Result card - cross_school_gov_consumption_unemployment_stabiliser_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher government consumption predicts lower unemployment.

## School Coverage

post_keynesian, new_keynesian, social_democratic

## What Was Measured

- Outcome: `unemployment`.
- Treatment: `gov_consumption`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,148 observations**, **173 countries**.
- Coefficient on treatment: **0.0445** (SE 0.0223, p=0.0457).

## Specification

`Q('unemployment') ~ Q('gov_consumption') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
