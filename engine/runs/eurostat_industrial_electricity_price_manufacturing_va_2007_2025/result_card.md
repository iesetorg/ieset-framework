# Result card - eurostat_industrial_electricity_price_manufacturing_va_2007_2025

**Verdict:** PARTIAL - coefficient is not statistically decisive at p<0.10.

## Plain-English Claim

Higher industrial electricity prices predict lower manufacturing value-added shares in European panels.

## School Coverage

classical_liberal, ordoliberal, developmentalism

## What Was Measured

- Outcome: `manufacturing_va_share`.
- Treatment: `industrial_electricity_price`.
- Controls: `gdp_pc_growth`.

## Results

- Usable panel: **170 observations**, **29 countries**, 2019-2024.
- Coefficient on treatment: **-5.2039** (SE 3.6301, p=0.1517).

## Specification

`Q('manufacturing_va_share') ~ Q('industrial_electricity_price') + Q('gdp_pc_growth') + C(country) + C(year)`

This is a short European panel screen using local landed vintages. Treat it as throughput evidence, not final causal proof.
