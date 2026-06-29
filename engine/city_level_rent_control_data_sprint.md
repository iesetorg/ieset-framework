# City-Level Rent-Control Data Sprint

Seeded: 2026-06-28

## Objective

Build enough city-level data coverage to turn rent control from a country-level
screen into a real local-policy test. The first usable milestone is not "all
top 1000 cities complete"; it is a repeatable city key, a ranked source
inventory, and 5-10 pilot cases where treatment, outcomes, supply response,
quality, leakage, and incidence can be measured.

## Current blocker

The pre-registered rent-control hypothesis already says the right thing:
country panels are screeners only. The missing data layers are local:

- regulated vs exempt rents
- permits, completions, rental listings, and rental-stock additions
- tenant mobility, waitlists, queue years, and time-to-lease
- maintenance complaints, code violations, inspections, and repair spending
- condominium conversion, owner-occupation shifts, demolitions, and short-term
  rental leakage
- income/tenure incidence for incumbents, entrants, uncovered renters,
  landlords, taxpayers, and future cohorts

## Research swarm map

Six agent tracks were launched:

| track | geography | main output |
| --- | --- | --- |
| North America | US, Canada, Mexico | rent-control, permits, rents, tenant protection, local open data |
| Europe | EU, UK, Switzerland, Nordics, broader Europe | Eurostat/OECD/national/local city housing panels |
| Latin America/Caribbean | large metro systems and municipal sources | rents, permits, cadastral/tenancy, local policy events |
| Asia-Pacific | East/South/Southeast Asia, Oceania | city housing outcomes, policy events, official local panels |
| Africa/MENA | Africa, Middle East, North Africa, Turkey | official city/municipal panels and policy sources |
| Global anchors | worldwide cross-city datasets | top-1000 city universe, boundaries, covariates, crosswalk strategy |

Integrated scout results so far:

| track | integrated files | status |
| --- | --- | --- |
| Global anchors | `data/city_level/source_inventory.yaml`, `data/city_level/README.md`, `data/city_level/ingestion_queue.yaml` | GHSL UCDB R2024A promoted to preferred city spine; UN WUP and GeoNames added as cross-check/matching layers |
| North America | `data/city_level/source_inventory.yaml`, `data/city_level/ingestion_queue.yaml` | LOCUS-v1, zoning, U.S. local registries, Canada outcomes/rent-guidelines, and Mexico API/price complements added as scout-reported records pending license/endpoint verification |
| Europe | `data/city_level/source_inventory.yaml`, `data/city_level/ingestion_queue.yaml` | France, Catalonia/Spain, Italy, Portugal, UK, Ireland, Germany, Nordic, and Inside Airbnb sources added as scout-reported records pending endpoint/schema verification |
| Latin America/Caribbean | `data/city_level/source_inventory.yaml`, `data/city_level/ingestion_queue.yaml` | Brazil, Mexico, Colombia, Chile, Peru, Argentina, Bogota, and IDB sources added as scout-reported records pending endpoint/codebook verification |
| Asia-Pacific | `data/city_level/source_inventory.yaml`, `data/city_level/ingestion_queue.yaml` | Korea, Japan, New Zealand, Australia, Singapore, Philippines, India, and China records added as scout-reported sources with proxy/direct-rent distinctions |
| Africa/MENA | `data/city_level/source_inventory.yaml`, `data/city_level/ingestion_queue.yaml` | Dubai, Saudi, South Africa/Cape Town, Israel, Turkey, Jordan, Tunisia, Morocco, Africapolis, Google Open Buildings, World Bank permits, and UrbanLex added as scout-reported records |

Pending scout integration: none from the initial six-agent swarm.

Generated tracking artifacts:

- `engine/city_level_source_index.json`
- `engine/city_level_source_index.md`
- `scripts/validate_city_level_sources.py`
- `scripts/generate_city_level_source_index.py`
- `scripts/build_city_spine_top1000.py`
- `tests/test_city_spine_builder.py`
- `scripts/build_us_zillow_city_rent_panel.py`
- `tests/test_us_zillow_city_rent_panel.py`
- `scripts/build_us_census_bps_city_permits_panel.py`
- `tests/test_us_census_bps_city_permits_panel.py`
- `data/derived/city_universe_top1000.parquet`
- `data/derived/city_crosswalks.parquet`
- `data/derived/us_city_rent_panel.parquet`
- `data/derived/us_city_permits_panel.parquet`

## Pilot cases

Start with cases that already appear in IESET hypotheses and positions:

| case | treatment | first data targets |
| --- | --- | --- |
| Berlin | Mietendeckel 2020-2021 | Mietspiegel, listings, permits/completions, donor German cities |
| San Francisco | 1994 rent-control expansion | DataSF permits/code/STR, Zillow, ACS, Census BPS |
| New York City | rent stabilization and HSTPA | NYC Open Data, ACS, BLS CPI rent, HUD, permits, HPD complaints |
| Stockholm | persistent rent controls and queue | Bostadsformedlingen statistics, SCB, municipal building data |
| St Paul | 2021 rent-stabilization ordinance | Zillow, Census BPS, ACS, local permits, Minneapolis comparison |
| Spain/Catalonia | Law 12/2023 stressed-market controls | rental reference system, municipality declarations, supply response |

## Ingestion priority

1. `ghsl_urban_centre_database`: city universe and geometry.
2. `un_world_urbanization_prospects_city_agglomerations`: official population cross-check.
3. `geonames_gazetteer`: aliases, coordinates, and stable place IDs.
4. `zillow_observed_rent_index`: monthly U.S. rent panel.
5. `us_census_building_permits_survey`: U.S. permit and supply response.
6. `us_acs_pums_summary`: incidence, mobility, rent burden, housing age.
7. `hud_fair_market_rents`: official U.S. rent benchmark.
8. `eurostat_cities_urban_audit`: European city covariates.
9. `uk_mhclg_house_building_live_tables`: district-level supply.
10. `nyc_open_data_housing_bundle`: NYC quality/supply/leakage.
11. `datasf_housing_bundle`: San Francisco quality/supply/leakage.
12. `stockholm_bostadsformedlingen_statistics`: Stockholm queue costs and rent-band counts landed from official JSON endpoints.
13. `dane_ipc_city_rent_items`: Colombia city housing/rent CPI variation layer landed from official DANE annexes.
14. `singapore_hdb_ura_rentals`: HDB median rents, HDB approval rents, and URA private non-landed rent distributions landed.
15. `hong_kong_rvd_private_domestic_rents_supply`: RVD private domestic rent-index and supply/vacancy annual panel landed.
16. `france_reference_rent_control_datasets`: Paris reference-rent legal floor/reference/ceiling cells landed from Opendatasoft export.
17. `sweden_scb_municipal_housing_pxweb`: Stockholm and Gothenburg municipal rents, completions, and dwelling stock landed from SCB PXWeb.
18. `dubai_land_department_rents`: Dubai residential rent-index, building permits, and completed-building supply rows landed from Data Dubai JSON endpoints.
19. `taiwan_moi_actual_price_rental_transactions`: Taiwan current rental transaction ZIP landed for Taipei, Taichung, Kaohsiung, Tainan, and Hsinchu top-1000 matches.

## Landed artifacts

- `scripts/build_city_spine_top1000.py`
- `scripts/build_city_policy_test_readiness_matrix.py`
- `scripts/build_catalonia_rent_contracts_panel.py`
- `scripts/build_france_reference_rents_panel.py`
- `scripts/build_stockholm_bostadsformedlingen_queue_panel.py`
- `scripts/build_sweden_scb_municipal_housing_panel.py`
- `scripts/build_dubai_data_housing_panel.py`
- `scripts/build_colombia_dane_ipc_city_rent_panel.py`
- `scripts/build_singapore_hdb_median_rent_panel.py`
- `scripts/build_singapore_hdb_ura_rental_panel.py`
- `scripts/build_hong_kong_rvd_private_domestic_panel.py`
- `scripts/build_taiwan_moi_rental_transactions_panel.py`
- `scripts/build_uk_ons_voa_private_rents_panel.py`
- `scripts/build_uk_mhclg_house_building_panel.py`
- `scripts/build_us_zillow_city_rent_panel.py`
- `scripts/build_us_census_bps_city_permits_panel.py`
- `scripts/build_nyc_open_data_housing_quality_panel.py`
- `scripts/build_nyc_rent_regulation_tax_benefit_panel.py`
- `scripts/build_datasf_housing_quality_panel.py`
- `scripts/build_us_acs_place_housing_incidence_panel.py`
- `engine/city_level_research_scout_notes_2026-06-28.md`
- `engine/city_level_research_scout_notes_2026-06-29.md`
- `engine/city_policy_test_readiness_summary.md`
- `tests/test_city_spine_builder.py`
- `tests/test_city_policy_test_readiness_matrix.py`
- `tests/test_catalonia_rent_contracts_panel.py`
- `tests/test_france_reference_rents_panel.py`
- `tests/test_colombia_dane_ipc_city_rent_panel.py`
- `tests/test_singapore_hdb_median_rent_panel.py`
- `tests/test_singapore_hdb_ura_rental_panel.py`
- `tests/test_hong_kong_rvd_private_domestic_panel.py`
- `tests/test_taiwan_moi_rental_transactions_panel.py`
- `tests/test_uk_ons_voa_private_rents_panel.py`
- `tests/test_uk_mhclg_house_building_panel.py`
- `tests/test_us_zillow_city_rent_panel.py`
- `tests/test_us_census_bps_city_permits_panel.py`
- `tests/test_nyc_open_data_housing_quality_panel.py`
- `tests/test_nyc_rent_regulation_tax_benefit_panel.py`
- `tests/test_datasf_housing_quality_panel.py`
- `tests/test_us_acs_place_housing_incidence_panel.py`
- `data/derived/city_universe_top1000.parquet`
- `data/derived/city_crosswalks.parquet`
- `data/derived/city_policy_test_readiness_matrix.parquet`
- `data/manifests/fetch_run_2026-06-29T000000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T010000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T030000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T040000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T060000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T080000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T100000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T120000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T140000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T160000Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-29T233000Z_city_policy_test_readiness.yaml`
- `data/derived/us_city_rent_panel.parquet`
- `data/derived/us_city_permits_panel.parquet`
- `data/derived/us_city_rent_control_quality_leakage_panel.parquet`
- `data/derived/nyc_rent_regulation_tax_benefit_panel.parquet`
- `data/derived/us_sf_rent_control_quality_leakage_panel.parquet`
- `data/derived/uk_ons_voa_private_rents_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T000000Z_uk_ons_voa_private_rents.yaml`
- `data/derived/uk_mhclg_house_building_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T020000Z_uk_mhclg_house_building.yaml`
- `data/derived/singapore_hdb_median_rent_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T050000Z_singapore_hdb_median_rent.yaml`
- `data/derived/singapore_hdb_ura_rental_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T070000Z_singapore_hdb_ura_rentals.yaml`
- `data/derived/hong_kong_rvd_private_domestic_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T090000Z_hong_kong_rvd_private_domestic.yaml`
- `data/derived/taiwan_moi_rental_transactions_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T230000Z_taiwan_moi_rental_transactions.yaml`
- `data/derived/france_reference_rents_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T110000Z_france_reference_rents.yaml`
- `data/raw/city_level/dane_ipc_annexes/manifest_2026-06-29.json`
- `data/derived/colombia_dane_ipc_city_rent_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T130000Z_colombia_dane_ipc_city_rent.yaml`
- `data/derived/catalonia_rent_contracts_panel.parquet`
- `data/manifests/fetch_run_2026-06-29T150000Z_catalonia_rent_contracts.yaml`

Expected after keyed ACS fetch:

- `data/derived/us_acs_place_housing_incidence_panel.parquet`

## Treatment registry fields

The local housing policy event registry should use these fields:

- `policy_event_id`
- `jurisdiction_name`
- `jurisdiction_type`
- `country_iso3`
- `city_crosswalk_ids`
- `policy_axis`
- `policy_family`
- `event_type`
- `effective_date`
- `repeal_or_suspension_date`
- `coverage_rule`
- `exemption_rule`
- `cap_formula`
- `enforcement_body`
- `enforcement_intensity`
- `source_url`
- `legal_text_url`
- `source_confidence`
- `notes`

## Promotion rule

No rent-control result should be promoted as dispositive unless at least four
layers are measured locally: first-order rent transfer, supply response,
quality or leakage, and distributional incidence. Queue/mobility and net
welfare should be required for flagship claims.
