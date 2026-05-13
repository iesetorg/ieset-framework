# Result card - eurostat_energy_price_export_competitiveness_panel

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher industrial electricity prices reduce export competitiveness.

## School Coverage

classical_liberal, developmentalism, ordoliberal

## What Was Measured

- Outcome: `export_share`.
- Treatment: `industrial_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **227 observations**, **39 countries**, 2019-2024.
- Coefficient on treatment: **-6.8845** (SE 10.8554, p=0.5259).

## Specification

`Q('export_share') ~ Q('industrial_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
