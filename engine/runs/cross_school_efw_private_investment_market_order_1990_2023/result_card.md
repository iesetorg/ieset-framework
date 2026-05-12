# Result card - cross_school_efw_private_investment_market_order_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Higher broad economic freedom predicts higher private-investment shares.

## School Coverage

austrian, classical_liberal, ordoliberal

## What Was Measured

- Outcome: `private_investment`.
- Treatment: `efw_summary`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **1,512 observations**, **87 countries**.
- Coefficient on treatment: **3.2136** (SE 0.7340, p=0.0000).

## Specification

`Q('private_investment') ~ Q('efw_summary') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
