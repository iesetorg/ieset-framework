# Result card - cross_school_fiscal_balance_private_investment_confidence_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Stronger fiscal balances predict higher private investment if confidence effects dominate.

## School Coverage

ordoliberal, post_keynesian

## What Was Measured

- Outcome: `private_investment`.
- Treatment: `fiscal_balance`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,151 observations**, **71 countries**.
- Coefficient on treatment: **0.0037** (SE 0.0078, p=0.6361).

## Specification

`Q('private_investment') ~ Q('fiscal_balance') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
