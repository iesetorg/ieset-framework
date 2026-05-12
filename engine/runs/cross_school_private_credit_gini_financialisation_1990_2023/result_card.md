# Result card - cross_school_private_credit_gini_financialisation_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Private-credit depth predicts higher income inequality.

## School Coverage

marxian, post_keynesian

## What Was Measured

- Outcome: `gini`.
- Treatment: `private_credit`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,771 observations**, **164 countries**.
- Coefficient on treatment: **0.0113** (SE 0.0055, p=0.0386).

## Specification

`Q('gini') ~ Q('private_credit') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
