# City-Level Source Index

Generated from `data/city_level/source_inventory.yaml` and `data/city_level/ingestion_queue.yaml`.

## Summary

- Sources indexed: 110
- Ingestion waves: 7
- Primary axis: `regulatory.housing_rent_control`
- Preferred city anchor: `ghsl_urban_centre_database`
- Verification statuses: `{"codebook_verified": 1, "endpoint_verified": 7, "scout_reported_unverified": 66, "seed_unverified_url": 7, "seed_verified_official_page": 29}`
- Ingestion difficulty: `{"high": 14, "low": 30, "medium": 66}`
- Top-1000 scalability: `{"high": 11, "low": 59, "medium": 40}`

## Most Covered Layers

- `distributional_incidence` (44)
- `first_order_price_or_transfer` (39)
- `implementation_capacity` (36)
- `second_order_supply_response` (33)
- `quality_margin` (29)
- `first_order_policy_effect` (21)
- `dynamic_investment_response` (13)
- `macro_feedback` (12)
- `allocation_distortion` (11)
- `externality_or_spillover` (5)
- `leakage_or_substitution` (4)
- `market_structure_response` (2)
- `fiscal_or_enforcement_cost` (1)
- `net_welfare` (1)

## Ingestion Waves

| wave | status | sources | target cases |
| --- | --- | ---: | --- |
| `city_spine_v0` | in_progress | 10 | - |
| `us_rent_control_pilot_v0` | in_progress | 15 | st_paul_rent_control_2021, sf_rent_control_1994, nyc_rent_stabilisation |
| `europe_rent_control_pilot_v0` | scout_reported_needs_verification | 16 | berlin_mietendeckel_2020, stockholm_rent_queue, spain_housing_law_12_2023, uk_renters_rights_act_2025 |
| `lac_municipal_housing_v0` | scout_reported_needs_verification | 18 | mexico_city_housing_policy_panel, sao_paulo_municipal_housing_policy_panel, bogota_affordability_quality_case, santiago_supply_response_panel |
| `apac_city_housing_v0` | scout_reported_needs_verification | 14 | korea_housing_lease_protection_act_city_panel, japan_city_housing_stock_rent_panel, australia_state_tenancy_law_city_panel, singapore_public_private_rental_split |
| `africa_mena_city_housing_v0` | scout_reported_needs_verification | 21 | dubai_rental_index_case, riyadh_jeddah_rent_indicator_panel, cape_town_zoning_permit_case, south_africa_municipal_housing_service_panel |
| `local_policy_event_registry_v0` | schema_design_ready | 5 | - |

## Top Ingestion Candidates

| rank | source | geography | difficulty | status | why it matters |
| ---: | --- | --- | --- | --- | --- |
| 1 | `ghsl_urban_centre_database` | global | low | seed_verified_official_page | canonical top-1000-city universe and spatial join anchor |
| 2 | `un_world_urbanization_prospects_city_agglomerations` | global | low | seed_verified_official_page | population-ranking cross-check for largest cities |
| 3 | `geonames_gazetteer` | global | low | seed_verified_official_page | city alias matching and stable gazetteer IDs |
| 4 | `eurostat_cities_urban_audit` | Europe | medium | seed_verified_official_page | comparable European city covariates and housing underlays |
| 5 | `oecd_regions_cities_metropolitan` | OECD and partner economies | medium | seed_verified_official_page | metro/FUA controls for high-income city panels |
| 6 | `zillow_observed_rent_index` | United States and selected geographies exposed by Zillow | low | seed_verified_official_page | first-order market-rent panel for US city and metro cases |
| 7 | `us_census_building_permits_survey` | United States | low | seed_verified_official_page | second-order supply response for US treated and donor cities |
| 8 | `hud_fair_market_rents` | United States | low | seed_verified_official_page | official rent benchmark and affordability control |
| 9 | `us_bls_cpi_area_rent` | United States | medium | seed_verified_official_page | official rent-inflation proxy for large U.S. metro cases |
| 10 | `us_acs_pums_summary` | United States | medium | codebook_verified | distributional incidence, mobility, and housing-quality proxies |
| 11 | `eviction_lab_eviction_tracking` | United States | medium | seed_verified_official_page | tenant-protection and allocation-distortion outcome layer |
| 12 | `local_housing_solutions_policy_library` | United States | high | seed_unverified_url | policy taxonomy and candidate local treatment discovery |
| 13 | `furman_land_use_reform_tracker` | United States | medium | scout_reported_unverified | treatment leads for housing-supply and land-use policy cases |
| 14 | `locus_v1_local_ordinance_corpus` | United States | high | scout_reported_unverified | scalable U.S. local-law treatment discovery through NLP |
| 15 | `national_zoning_atlas` | United States | high | scout_reported_unverified | zoning and supply-restriction control/treatment layer |
| 16 | `grounded_solutions_inclusionary_housing` | United States | high | scout_reported_unverified | adjacent housing-policy event source and local policy controls |
| 17 | `wharton_land_use_regulation_index` | United States | high | scout_reported_unverified | zoning restrictiveness control for U.S. rent-control donor pools |
| 18 | `uk_mhclg_house_building_live_tables` | England and UK tables depending on file | low | seed_verified_official_page | local supply response and donor controls for UK housing policies |
| 19 | `nyc_open_data_housing_bundle` | New York City | medium | endpoint_verified | NYC rent-stabilization quality, stock, and leakage layers |
| 20 | `datasf_housing_bundle` | San Francisco | medium | endpoint_verified | San Francisco 1994 expansion supply, conversion, and quality layers |
| 21 | `berlin_mietspiegel` | Berlin | medium | seed_unverified_url | Berlin regulated-market rent benchmark around Mietendeckel |
| 21 | `nyc_open_data_tax_benefit_regulation_bundle` | New York City | medium | endpoint_verified | NYC rent-stabilization treatment-coverage proxy and regulated-stock denominator |
| 22 | `stockholm_bostadsformedlingen_statistics` | Stockholm region | medium | seed_unverified_url | allocation-distortion and queue-cost layer for Stockholm |
| 23 | `spain_rental_reference_price_system` | Spain | high | seed_unverified_url | treatment intensity and first-order cap benchmark for Spain Law 12/2023 |
| 24 | `apartment_list_rent_estimates` | United States | medium | scout_reported_unverified | alternative first-order rent panel for U.S. cities |
| 25 | `eviction_lab_tracking_system` | selected United States metros and cities | medium | scout_reported_unverified | high-frequency tenant-protection outcome around policy changes |
| 26 | `nyc_rent_guidelines_board_stabilized_lists` | New York City | medium | scout_reported_unverified | NYC treatment registry exemplar for rent stabilization |
| 27 | `la_rso_open_data` | Los Angeles | medium | scout_reported_unverified | major-city treatment registry exemplar |
| 28 | `dc_rent_control_registration_open_data` | Washington, DC | medium | scout_reported_unverified | U.S. rent-control treatment and registry exemplar |
| 29 | `seattle_rrio_rental_registry` | Seattle | medium | scout_reported_unverified | rental-registry infrastructure control case without rent control |
