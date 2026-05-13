# Result card - cross_school_capital_openness_fdi_1990_2023

**Verdict:** PARTIAL - coefficient is not statistically decisive at p <= 0.10.

## Plain-English Claim

Capital-account openness predicts higher FDI inflows.

## School Coverage

austrian, classical_liberal, ordoliberal

## What Was Measured

- Outcome: `fdi`.
- Treatment: `kaopen`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **5,660 observations**, **179 countries**.
- Coefficient on treatment: **10.1027** (SE 6.5549, p=0.1233).

## Specification

`Q('fdi') ~ Q('kaopen') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a cross-country panel screen with country and year fixed effects. Treat it as throughput evidence, not final causal proof.
