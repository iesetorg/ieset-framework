# Result card - cross_school_regulation_employment_market_order_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

More flexible regulation predicts higher employment-to-population ratios.

## School Coverage

classical_liberal, chicago_monetarism, ordoliberal

## What Was Measured

- Outcome: `employment`.
- Treatment: `efw_regulation`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **4,035 observations**, **163 countries**.
- Coefficient on treatment: **-0.3137** (SE 0.3917, p=0.4232).

## Specification

`Q('employment') ~ Q('efw_regulation') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
