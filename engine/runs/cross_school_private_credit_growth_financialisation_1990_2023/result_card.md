# Result card - cross_school_private_credit_growth_financialisation_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Private-credit depth does not reliably translate into faster GDP per-capita growth.

## School Coverage

marxian, post_keynesian

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `private_credit`.
- Controls: none.

## Results

- Usable panel: **4,905 observations**, **186 countries**.
- Coefficient on treatment: **-0.0448** (SE 0.0091, p=0.0000).

## Specification

`Q('gdp_pc_growth') ~ Q('private_credit') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
