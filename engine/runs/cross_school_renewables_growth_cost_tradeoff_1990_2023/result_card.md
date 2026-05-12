# Result card - cross_school_renewables_growth_cost_tradeoff_1990_2023

**Verdict:** SUPPORTED - coefficient has the predeclared sign and p <= 0.10.

## Plain-English Claim

Higher renewable-electricity shares predict faster GDP per-capita growth.

## School Coverage

eco_socialist, classical_liberal

## What Was Measured

- Outcome: `gdp_pc_growth`.
- Treatment: `renewable_electricity`.
- Controls: none.

## Results

- Usable panel: **5,584 observations**, **206 countries**.
- Coefficient on treatment: **0.0249** (SE 0.0131, p=0.0579).

## Specification

`Q('gdp_pc_growth') ~ Q('renewable_electricity') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
