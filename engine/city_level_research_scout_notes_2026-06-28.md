# City-Level Research Scout Notes, 2026-06-28

These notes preserve the parallel scout findings behind the city-level rent
control data sprint. They are not production manifests; promote entries into
`data/city_level/source_inventory.yaml` before writing fetchers.

## DataSF Follow-Ups

The landed DataSF panel uses `i98e-djp9`, `gm2e-bten`, `nbtm-fbw5`,
`gdc7-dmcn`, `6swy-cmkq`, `5cei-gny5`, and `wmam-7g8d`.

High-value follow-up DataSF views:

- `f2jc-ivnc`: Building Permits Deduplicated on Primary Address.
- `j67f-aayr`: Dwelling Unit Completion Counts by Building Permit.
- `6jgi-cpb4`: San Francisco Development Pipeline.
- `xdht-4php`: Housing Production - 2005-present.
- `vckc-dh2h`: Building Inspections.
- `vw6y-z8j6`: 311 Cases; weak short-term-rental complaint proxy.
- `wv5m-vpq2`: Assessor Historical Secured Property Tax Rolls.
- `pa56-ek2h`: Assessor Property Class Codes.
- `acdm-wktn`: Parcels - Active and Retired.
- `c5ge-t6pj`: San Francisco Land Use.
- `hsxb-ci7b`: Annual Allowable Rent Increase for Units Under Rent Control.

Gotchas: building permits can duplicate across addresses, eviction notices are
not confirmed evictions, and analysis neighborhoods are tract groupings rather
than legal boundaries.

## NYC Rent Regulation Follow-Ups

The landed NYC panel covers DOB permits, HPD complaints/problems, and HPD
violations. The scout found no public bulk apartment-level DHCR/HCR rent
registration file. Practical public proxies are building lists, Rent Guidelines
Board orders/reports, and tax-benefit datasets.

High-value NYC sources:

- `nyc_rgb_hcr_registered_building_lists`: RGB borough PDF building lists.
- `nyc_rgb_apartment_orders`: Apartment/loft guideline orders.
- `nyc_rgb_stock_changes_reports`: annual reports on stabilized stock changes.
- `nyc_dof_property_exemption_detail`: NYC Open Data `muvi-b6kx`.
- `nyc_dof_exemption_classification_codes`: NYC Open Data `myn9-hwsy`.
- `nyc_dof_property_abatement_detail`: NYC Open Data `rgyu-ii48`.
- `nyc_dof_j51_historical`: NYC Open Data `y7az-s7wc`.
- `nyc_hpd_421a16_completion_extension_letters`: NYC Open Data `pq4c-wbq4`.
- `nyc_hpd_485x_registrations`: NYC Open Data `rrtd-iyd7`.
- `nyc_dcp_pluto_tax_lot`: NYC Open Data `64uk-42ks`.
- `nyc_hpd_multiple_dwelling_registrations`: NYC Open Data `tesw-yqqr`.
- `nyc_hpd_ll7_qualified_transactions`: NYC Open Data `8wi4-bsy4`.
- `nyc_hpd_speculation_watch_list`: NYC Open Data `adax-9mit`.

First NYC stock plan: build RGB registered-building stock, tax-benefit
regulation proxy, and RGB guideline-order annual series. Join by normalized
10-digit BBL, with BIN/building ID as secondary keys.

## U.S. National Local Layers

Priority order:

1. ACS 5-year place and tract incidence panel for rent burden, tenure, income,
   vacancy, mobility, housing age, and structure type. Census API calls require
   an API key.
2. HUD FMR/SAFMR official rent benchmarks. Prefer bulk downloads where
   available; HUD API requires token authentication.
3. Eviction Lab tracking and historical eviction layers.
4. Census HVS metro vacancy series as robustness checks.
5. BLS CPI rent/OER series by CPI area as coarse official rent inflation
   robustness.

Crosswalk plan: keep a bridge table with GHSL urban-centre ID, native
geography type/ID, year, area/population weights, match method, and review
flags. Treat county, CBSA, CPI-area, and ZIP/ZCTA benchmarks as contextual
layers rather than municipal treatment outcomes.
