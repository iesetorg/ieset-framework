# Result card - cross_school_public_debt_inflation_mmt_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Public debt does not mechanically predict higher inflation.

## School Coverage

mmt, post_keynesian

## What Was Measured

- Outcome: `inflation`.
- Treatment: `public_debt`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,576 observations**, **105 countries**.
- Coefficient on treatment: **0.8376** (SE 2.0967, p=0.6895).

## Specification

`Q('inflation') ~ Q('public_debt') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
