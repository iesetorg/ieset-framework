# Batch 06 Eurostat Energy Prices / Nuclear Transition Readiness Audit - 2026-05-12

- Promoted specs: 10
- Runnable results written: 8
- Blocked IDs: 2
- Verdict tally: {'PARTIAL': 7, 'SUPPORTED': 1}

## Local Inventory

- Eurostat `nrg_pc_205`: present; industrial electricity prices by semester, consumption band, tax, currency, country.
- Eurostat sectoral/labour: `nama_10_a10_e` and `une_rt_a` present; national panels are usable, regional unemployment design was downgraded to national overlap.
- IRENA: renewable capacity and LCOE vintages present; capacity is inventoried, while LCOE is world-only and not suitable for country fixed effects.
- WDI: manufacturing value added, CPI inflation, exports, GDP growth, population, sector employment proxies present.

## Runnable Results

- `eurostat_industrial_electricity_price_manufacturing_va_2007_2025`: PARTIAL (221 obs, 38 countries, p=0.1398).
- `eurostat_electricity_price_inflation_pass_through`: SUPPORTED (226 obs, 39 countries, p=0.0307).
- `eurostat_nuclear_retention_industrial_price_panel`: PARTIAL (227 obs, 39 countries, p=0.7429).
- `eurostat_renewable_share_electricity_price_transition_cost`: PARTIAL (227 obs, 39 countries, p=0.3567).
- `eurostat_energy_price_export_competitiveness_panel`: PARTIAL (227 obs, 39 countries, p=0.5259).
- `eurostat_energy_price_unemployment_regional_panel`: PARTIAL (198 obs, 34 countries, p=0.8065).
- `eurostat_electricity_price_volatility_industrial_exit`: PARTIAL (192 obs, 33 countries, p=0.2269).
- `eurostat_energy_price_services_vs_industry_reallocation`: PARTIAL (192 obs, 33 countries, p=0.5942).

## Blockers

- `eurostat_household_electricity_price_consumption_panel`: Local Eurostat inventory has nrg_pc_205 industrial prices only; nrg_pc_204 household electricity prices are not present.
- `eurostat_energy_price_household_distribution_stress`: No local household electricity-price vintage, EU-SILC distribution table, or poverty stress panel was present for this batch.
