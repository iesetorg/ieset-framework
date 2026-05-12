# Result card - cross_school_private_credit_manufacturing_financialisation_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Private-credit depth predicts manufacturing-share erosion, consistent with financialisation crowding out production.

## School Coverage

marxian, market_socialist, post_keynesian

## What Was Measured

- Outcome: `manufacturing_share`.
- Treatment: `private_credit`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **4,378 observations**, **181 countries**.
- Coefficient on treatment: **-0.0173** (SE 0.0097, p=0.0748).

## Specification

`Q('manufacturing_share') ~ Q('private_credit') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
