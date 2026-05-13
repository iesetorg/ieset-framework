# Result card - eurostat_energy_price_unemployment_regional_panel

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher industrial electricity prices predict higher unemployment in European labour-market panels.

## School Coverage

post_keynesian, ordoliberal, empirical_pragmatist

## What Was Measured

- Outcome: `unemployment_rate`.
- Treatment: `industrial_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **198 observations**, **34 countries**, 2019-2024.
- Coefficient on treatment: **0.5976** (SE 2.4391, p=0.8065).

## Specification

`Q('unemployment_rate') ~ Q('industrial_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
