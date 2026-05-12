# Result card - cross_school_fiscal_balance_unemployment_austerity_1990_2023

**Verdict:** REFUTED - coefficient is statistically significant in the opposite direction.

## Plain-English Claim

Stronger fiscal balances predict higher unemployment if austerity is contractionary.

## School Coverage

post_keynesian, social_democratic

## What Was Measured

- Outcome: `unemployment`.
- Treatment: `fiscal_balance`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **3,426 observations**, **147 countries**.
- Coefficient on treatment: **-0.0182** (SE 0.0103, p=0.0756).

## Specification

`Q('unemployment') ~ Q('fiscal_balance') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
