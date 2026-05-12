# Result card - cross_school_trade_openness_growth_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Trade openness predicts faster real GDP per-capita growth.

## School Coverage

classical_liberal, developmentalism

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `trade_open`.
- Controls: none.

## Results

- Usable panel: **5,729 observations**, **191 countries**.
- Coefficient on treatment: **0.0111** (SE 0.0066, p=0.0900).

## Specification

`Q('gdp_pc_growth') ~ Q('trade_open') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
