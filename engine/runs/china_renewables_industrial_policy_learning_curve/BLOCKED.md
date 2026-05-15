# BLOCKED - china_renewables_industrial_policy_learning_curve

**Status:** Diagnostic revived; original CHN-vs-OECD mechanism test remains blocked.

## Local coverage check

- `data/manual/irena/` exists but is empty.
- IRENA capacity vintages are present and loadable:
  - `irena:installed_capacity_renewable`
  - `irena:installed_capacity_solar_pv`
  - `irena:installed_capacity_wind`
- IRENA LCOE vintages are now present and loadable:
  - `data/vintages/irena/lcoe_solar_pv@2026-05-12T125721Z.parquet`
  - `data/vintages/irena/lcoe_wind_onshore@2026-05-12T125721Z.parquet`
- Those LCOE vintages contain `country = World` rows only. They are suitable for a transparent global learning-curve revival, but not for the pre-registered CHN-vs-OECD cohort comparison.

## Required source files

- For the original falsification test, add country/cohort-level solar and wind LCOE covering CHN and the OECD comparator pool. Candidate sources are BNEF, IEA, or any official IRENA companion data if a country-level workbook is available.
- Required columns after parsing: country or cohort, year, technology, and LCOE value. Units should be USD/MWh.
- 2026-05-15 revival note: `replication.py` now estimates the safe narrower world-aggregate learning curve from exact local IRENA LCOE and capacity vintages, but keeps the verdict inconclusive for the original hypothesis.

## Action

Do not grade the original China industrial-policy claim from the world-only LCOE series. A final high-integrity verdict should use a dedicated learning-curve replication (log LCOE on log technology-specific cumulative capacity, CHN vs OECD) after country/cohort LCOE is available.
