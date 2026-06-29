# City-Level Research Scout Notes, 2026-06-29

These notes preserve the Europe, Latin America, and Asia-Pacific scout returns
for the top-1000 city rent-control data sprint. Source records promoted from
this note should still have endpoints, codebooks, and licensing rechecked at
fetch time.

## Europe

Best first wave:

- `france_oll_rent_observations`: data.gouv national OLL CSVs with local rent
  observations by agglomeration/city-centre, dwelling type, construction epoch,
  room count, occupation age, and year.
- `france_reference_rent_control_datasets`: Paris reference-rent control data,
  Opendatasoft API, with annual zones/neighborhoods, dwelling attributes, and
  reference/min/max rents from 2019 onward.
- `france_sitadel_permits`: Sitadel permit life-cycle data since 2013 by
  commune/parcel/project.
- `catalonia_housing_open_data_bundle`: Generalitat Socrata rental contracts
  and average contractual rent by municipality/quarter; high payoff for Spain
  Law 12/2023 tense-market tests.
- `uk_ons_voa_private_rents` and `uk_mhclg_house_building_live_tables`:
  local-authority rent and starts/completions layers.
- `sweden_scb_municipal_housing_pxweb`: promoted from scout return as the
  scalable Swedish municipal housing-stock/supply companion to Stockholm queue
  statistics.

Case-heavy follow-ups: Berlin Mietspiegel, Germany Regionalstatistik/INKAR,
Stockholm Bostadsformedlingen queue statistics, Ireland RTB/RPZ, Portugal INE
municipal rents, and Italy OMI quotations.

## Latin America

Best first wave:

- `mexico_sniiv_sedatu`: Mexican municipal supply/program panel with monthly
  CSV/XLSX/API routes.
- `inegi_banco_indicadores_api` and `inegi_cpv_scince`: Mexican municipal
  tenure, rent, vacancy, and housing-condition baselines.
- `ibge_munic`: Brazilian municipal policy/implementation backbone.
- `ibge_ipca_snicp_residential_rent`: Brazil official CPI residential-rent
  item by SNIPC area, a rent-index proxy for major metros.
- `dane_elic` and `dane_ceed`: Colombian municipal construction licenses and
  realized construction pipeline.
- `dane_ipc_city_rent_items`: promoted from scout return as Colombia's official
  city rent/housing CPI layer across the CPI city system.
- `dane_cnpv_2018_housing`: Colombian municipal housing denominator and
  incidence layer.
- `chile_ine_building_permits`: Chile comuna supply panel.

Deep case follow-ups: Bogota multipurpose survey/cadastre, Sao Paulo GeoSampa
cadastre/zoning, Rio Data.Rio housing/land-use bundle, Buenos Aires housing
observatory, Colombia Ley 820 rent regime, Argentina rent-law shocks, and CDMX
rent-policy/legal sources.

## Asia-Pacific

Best first wave:

- `korea_molit_rtms_rent_api`: apartment rent/jeonse contracts by sigungu/dong.
- `japan_estat_housing_land_survey`: municipality Housing and Land Survey
  rents, rented stock, vacancies, and rent per square metre.
- `nz_tenancy_rental_bond_data`: monthly rents and bonds by TA/region/SA2.
- `hong_kong_rvd_private_domestic_rents_supply`: RVD rents, indices, supply,
  stock, vacancy, and take-up.
- `singapore_hdb_ura_rentals`: HDB town/flat rents and URA private rentals.
- `taiwan_moi_actual_price_rental_transactions`: actual-price rental
  transaction downloads.
- `australia_state_rental_bond_panels` and
  `abs_building_approvals_census_housing`: Australian rent and supply layers.
- `japan_mlit_national_land_numerical_info`: promoted for Japan land-use,
  zoning, boundary, and land-price covariates.
- `china_nbs_70city_housing_price_supply`: promoted as a Chinese official
  price/supply proxy, not observed rent.
- `india_nhb_residex_city_hpi`: promoted as the clean Indian official city HPI
  proxy before harder CPI-IW housing/rent parsing.

Global scalable companions: Overture Maps, geoBoundaries, OSM/Geofabrik, GHSL
built/pop grids, Google Open Buildings, WorldPop, and VIIRS night lights.

Policy overlays to code separately: Korea Housing Lease Protection Act, New
Zealand Residential Tenancies Act events, Australian state tenancy-law events,
Hong Kong subdivided-units rent-control events, and OECD affordable-housing
rent-regulation summaries. Treat national overlays as exposure designs unless
there is municipal variation.

Latest APAC scout ranking:

1. Korea MOLIT RTMS apartment rent/lease API: best observed-rent target for
   Seoul/Gyeonggi/Incheon district-month panels, but requires a data.go.kr
   service key.
2. Taiwan MOI actual transaction rentals: strong credential-free transaction
   download target after Chinese schema/city-code handling.
3. Singapore HDB/URA rentals: HDB median rents, HDB approval rents, and URA
   private non-landed rent distributions are now landed; remaining work is
   subcity geometry/postal-district exposure.
4. Australia state rental-bond panels: Victoria CKAN XLSX resources are the
   clean first state target.
5. Hong Kong RVD private domestic rents/supply: long XLS history, with reuse
   terms still to verify.
