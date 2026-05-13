# Result card - cross_school_trade_openness_manufacturing_developmental_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Trade openness predicts higher manufacturing value-added share.

## School Coverage

developmentalism, classical_liberal

## What Was Measured

- Outcome: `manufacturing_share`.
- Treatment: `trade_open`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,062 observations**, **182 countries**.
- Coefficient on treatment: **0.0084** (SE 0.0081, p=0.3004).

## Specification

`Q('manufacturing_share') ~ Q('trade_open') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
