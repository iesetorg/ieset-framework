# Result card - cross_school_efw_growth_market_order_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Higher broad economic freedom predicts faster real GDP per-capita growth.

## School Coverage

austrian, classical_liberal, chicago_monetarism, ordoliberal

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `efw_summary`.
- Controls: none.

## Results

- Usable panel: **4,092 observations**, **164 countries**.
- Coefficient on treatment: **0.6849** (SE 0.3830, p=0.0738).

## Specification

`Q('gdp_pc_growth') ~ Q('efw_summary') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
