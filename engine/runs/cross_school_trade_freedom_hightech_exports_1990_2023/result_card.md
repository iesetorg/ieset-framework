# Result card - cross_school_trade_freedom_hightech_exports_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Freedom to trade predicts higher high-tech export intensity.

## School Coverage

classical_liberal, developmentalism, ordoliberal

## What Was Measured

- Outcome: `high_tech_exports`.
- Treatment: `efw_trade`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **2,229 observations**, **159 countries**.
- Coefficient on treatment: **0.1395** (SE 0.3308, p=0.6733).

## Specification

`Q('high_tech_exports') ~ Q('efw_trade') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
