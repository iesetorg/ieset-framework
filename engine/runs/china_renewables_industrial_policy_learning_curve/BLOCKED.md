# BLOCKED - china_renewables_industrial_policy_learning_curve

**Status:** Cannot graduate with currently-fetched local data.

## Local coverage check

- `data/manual/irena/` exists but is empty.
- IRENA capacity vintages are now present and loadable:
  - `irena:installed_capacity_renewable`
  - `irena:installed_capacity_solar_pv`
  - `irena:installed_capacity_wind`
- `data/fetchers/irena.py` supports the canonical aliases needed by this spec: `lcoe_solar_pv`, `lcoe_wind_onshore`, and `installed_capacity_renewable`.
- The current `diagnostics.json` therefore remains an LCOE outcome-data blocker, not a capacity-data blocker.

## Required source files

- IRENA, `Renewable Power Generation Costs in 2024`, `Download data` workbook from https://www.irena.org/publications/2025/Jun/Renewable-Power-Generation-Costs-in-2024. Drop the XLSX/CSV under `data/manual/irena/` with a filename containing `solar` or `wind`, or adapt `data/fetchers/irena.py` to parse the workbook sheets directly.
- Required columns after parsing: country or region, year, technology, and LCOE value. The runner expects normalised parquet rows with `country_iso3`, `year`, and `value`; units should be USD/MWh.
- Capacity no longer blocks the run; the remaining primary missing vintages are `irena:lcoe_solar_pv` and `irena:lcoe_wind_onshore`.
- 2026-05-04 network note: the official IRENA publication page and costs-topic pages are readable via browser/search snippets, but direct `curl` from this environment receives `403 Forbidden` from the Azure gateway. Do not reconstruct LCOE vintages from report snippets; use the official downloaded workbook or a first-class parser for the official data companion.

## Action

Descriptive smoke reruns still remain inconclusive because LCOE outcomes are absent. A final high-integrity verdict should use a dedicated learning-curve replication (log LCOE on log technology-specific cumulative capacity, CHN vs OECD) after the official LCOE workbook is available.
