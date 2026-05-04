# BLOCKED - fossil_subsidy_persistence_private_ownership_link

**Status:** Cannot rerun with currently-fetched local data.

## Local coverage check

- No `data/manual/iea/` fossil-subsidy manual drop is present.
- No `data/vintages/iea/*.parquet` files are present.
- No local IMF energy-subsidy vintage exists for `imf:imf_energy_subsidies`.
- The IEA source id in the spec has been normalised to the local fetcher-supported `iea:fossil_subsidies_estimate`; this prevents the next rerun from missing the IEA workbook due only to an alias mismatch.

## Required source files

- IEA, `Fossil Fuel Subsidies Database`, file `Subsidies 2010-2024.xlsx` from https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database. Drop it at `data/manual/iea/fossil_subsidies_estimate/Subsidies 2010-2024.xlsx`, then run the IEA fetcher to create `data/vintages/iea/fossil_subsidies_estimate@<UTC>.parquet`.
- IMF, `Fossil Fuel Subsidies by Country and Fuel Database (2025)` or the `IMF Fossil Fuel Subsidies Data: 2023 Update` accompanying spreadsheets from https://www.imf.org/en/topics/climate-change/energy-subsidies. Convert the country-year explicit / total subsidy pct-GDP fields into `data/vintages/imf/imf_energy_subsidies@<UTC>.parquet`.
- Private fossil-reserve ownership remains unresolved: the spec cites `academic:rystad_global_reserves_ownership`, and no Rystad manual coding sheet is present. This is a treatment/mechanism blocker after the outcome gate is resolved.

## Action

No descriptive rerun was performed. Outcome coverage is still absent, so rerunning would only refresh an inconclusive timestamp.
