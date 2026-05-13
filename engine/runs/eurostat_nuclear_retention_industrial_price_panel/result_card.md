# Result card - eurostat_nuclear_retention_industrial_price_panel

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Countries retaining higher nuclear-electricity shares have lower industrial electricity prices.

## School Coverage

ordoliberal, developmentalism, eco_socialist

## What Was Measured

- Outcome: `industrial_electricity_price`.
- Treatment: `nuclear_share`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **227 observations**, **39 countries**, 2019-2024.
- Coefficient on treatment: **-0.0005** (SE 0.0014, p=0.7429).

## Specification

`Q('industrial_electricity_price') ~ Q('nuclear_share') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
