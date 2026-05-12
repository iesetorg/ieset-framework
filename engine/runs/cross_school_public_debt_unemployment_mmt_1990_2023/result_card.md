# Result card - cross_school_public_debt_unemployment_mmt_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Higher public debt is associated with lower unemployment if deficits accommodate demand.

## School Coverage

mmt, post_keynesian

## What Was Measured

- Outcome: `unemployment`.
- Treatment: `public_debt`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,478 observations**, **101 countries**.
- Coefficient on treatment: **0.0263** (SE 0.0092, p=0.0042).

## Specification

`Q('unemployment') ~ Q('public_debt') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
