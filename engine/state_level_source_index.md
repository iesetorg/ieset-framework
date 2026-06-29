# State-Level Source Index

Generated from `data/state_level/source_inventory.yaml` and `data/state_level/ingestion_queue.yaml`.

## Summary

- Sources indexed: 59
- Ingestion waves: 6
- Primary scope: `admin1_subnational_policy_panels`
- Preferred state anchor: `geoboundaries_admin1`
- Verification statuses: `{"endpoint_verified": 1, "license_verified": 2, "production_ready": 5, "scout_reported_unverified": 6, "seed_unverified_url": 22, "seed_verified_official_page": 23}`
- Ingestion difficulty: `{"high": 12, "low": 13, "medium": 34}`
- Admin1 scalability: `{"high": 7, "medium": 52}`

## Policy Domains

- `economic_accounts` (33)
- `labor` (32)
- `demography` (28)
- `housing` (22)
- `fiscal` (18)
- `health` (17)
- `education` (16)
- `admin_spine` (7)
- `policy_events` (7)
- `environment_energy` (5)
- `transport` (3)
- `crime_justice` (1)

## Ingestion Waves

| wave | status | sources | target cases |
| --- | --- | ---: | --- |
| `state_spine_v0` | in_progress | 10 | - |
| `us_state_labor_policy_v0` | in_progress | 9 | high_bite_minimum_wage_state_did, state_labor_market_deregulation_panel, state_wage_distribution_incidence_panel |
| `us_state_housing_fiscal_v0` | ready_for_fetcher_design | 17 | state_housing_supply_reform_panel, state_tax_spending_growth_panel, state_energy_policy_outcome_panel, state_health_education_spending_incidence_panel |
| `oecd_europe_regional_v0` | scout_reported_needs_verification | 13 | germany_lander_policy_panel, swiss_canton_policy_panel, canada_province_policy_panel, eurostat_nuts_policy_controls |
| `federal_systems_admin1_v0` | scout_reported_needs_verification | 17 | brazil_uf_policy_panel, mexico_state_policy_panel, india_state_reform_panel, china_provincial_housing_macro_panel, ... |
| `state_policy_event_registry_v0` | schema_design_ready | 9 | state_minimum_wage_events, state_rent_control_preemption_events, state_energy_policy_events, state_tax_spending_events |

## Top Ingestion Candidates

| rank | source | geography | difficulty | status | why it matters |
| ---: | --- | --- | --- | --- | --- |
| 1 | `geoboundaries_admin1` | global | medium | seed_unverified_url | canonical global admin1 boundary and crosswalk anchor |
| 2 | `gadm_admin1` | global | medium | seed_unverified_url | fallback global admin1 geometry and name/code crosswalk |
| 3 | `iso_3166_2_subdivisions` | global | high | seed_unverified_url | stable public-facing code namespace for admin1 IDs and crosswalks |
| 4 | `natural_earth_admin1` | global | low | seed_unverified_url | lightweight global admin1 map and coarse crosswalk fallback |
| 5 | `usdol_state_minimum_wage_history` | United States | low | production_ready | treatment source and v0 U.S. admin1 spine seed |
| 6 | `bls_lau_state_labor_force` | United States | low | production_ready | labor-market outcome layer for U.S. state policy panels |
| 7 | `bls_oews_state_wage` | United States | low | production_ready | wage denominator and wage-distribution outcome layer |
| 8 | `bls_qcew_state_employment_wages` | United States | low | production_ready | employment, industry, and wage outcomes for state policy tests |
| 9 | `derived_minimum_wage_bite_ratio_subnational_panel` | United States | low | production_ready | treatment intensity layer for high-bite minimum-wage tests |
| 10 | `us_census_state_population_estimates` | United States | low | seed_unverified_url | denominator/control layer for state panels |
| 11 | `us_census_acs_state_profile` | United States | medium | seed_unverified_url | distributional incidence and control layer for U.S. state policy tests |
| 12 | `bea_sagdp_state_accounts` | United States | medium | seed_unverified_url | macro outcome and control layer for U.S. state panels |
| 13 | `us_census_bps_state_permits` | United States | low | seed_unverified_url | housing-supply response layer for state housing and land-use policies |
| 14 | `eia_state_energy_data_system` | United States | medium | seed_unverified_url | energy-policy outcome layer for state climate, price, and regulation tests |
| 15 | `cdc_wonder_state_health` | United States | high | seed_unverified_url | health outcome layer for Medicaid, public-health, and welfare state tests |
| 16 | `nces_state_education_data` | United States | medium | seed_unverified_url | education-policy outcome and fiscal-control layer |
| 17 | `fbi_cde_state_crime` | United States | high | seed_unverified_url | crime and justice outcome layer for state policy panels |
| 18 | `nasbo_state_expenditure_report` | United States | medium | seed_unverified_url | fiscal-treatment and fiscal-control layer for U.S. state panels |
| 19 | `ncsl_state_policy_database` | United States | high | scout_reported_unverified | broad state policy-event discovery layer before official legal-text coding |
| 20 | `oecd_regional_statistics` | OECD and partner economies | medium | seed_unverified_url | high-income regional outcome and control layer |
| 21 | `eurostat_nuts_regional_statistics` | European Union and associated statistical territories | medium | seed_unverified_url | European regional panel layer and NUTS-to-admin1 bridge |
| 22 | `destatis_regional_lander_data` | Germany | medium | seed_unverified_url | Germany Laender outcome layer for federal/state policy cases |
| 23 | `statcan_provincial_territorial_statistics` | Canada | medium | seed_unverified_url | Canadian province/territory panels for federal-system comparisons |
| 24 | `abs_state_territory_statistics` | Australia | medium | seed_unverified_url | Australia state/territory outcomes for tenancy, labor, and housing reforms |
| 25 | `australia_state_rental_bond_panels` | Australia | high | scout_reported_unverified | direct rent outcome layer for Australian state tenancy-law designs |
| 26 | `ibge_sidra_uf` | Brazil | medium | seed_unverified_url | Brazil UF outcome/control layer and municipal bridge |
| 27 | `inegi_state_indicators` | Mexico | medium | seed_unverified_url | Mexico state outcome/control layer and municipality bridge |
| 28 | `india_mospi_state_domestic_product` | India | high | scout_reported_unverified | India state/UT macro outcome layer for reform and federal policy cases |
| 29 | `china_nbs_provincial_statistics` | China | high | scout_reported_unverified | China provincial macro and housing outcome layer |
| 30 | `statssa_provincial_data` | South Africa | medium | scout_reported_unverified | South Africa provincial outcome layer and municipal bridge |
