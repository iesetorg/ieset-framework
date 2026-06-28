# City-Level Data Expansion

This directory tracks the city-level data sprint opened on 2026-06-28. The
immediate target is rent-control testing, but the structure is broader: build a
top-1000-world-cities panel that can support local housing, land-use,
transport, policing, climate, and fiscal policy tests.

## Why this exists

IESET already has thousands of policy entries and a strong country-level data
substrate. Rent control is the clearest place where country panels fail: the
treatment is local, exemptions are local, and the second-order outcomes are
local. The existing `regulatory.housing_rent_control` axis correctly requires
regulated-vs-exempt rents, permits, listings, conversions, vacancy/queue
measures, quality complaints, and distributional incidence. This directory is
the data-discovery layer for those requirements.

## Canonical city key

Use a separate city identity spine before writing fetchers:

1. Start with `ghsl_urban_centre_database` as the global geometry/population
   anchor, using GHSL UCDB R2024A unless a newer release is intentionally
   pinned.
2. Rank the largest 1000 urban centres by 2025 GHSL population.
3. Store stable crosswalks to UN WUP agglomerations, OECD FUAs, Eurostat city
   IDs, national statistical IDs, GeoNames IDs, Wikidata QIDs, OSM relation IDs,
   and publisher native IDs.
4. Separate morphological cities, administrative municipalities, and functional
   metros. Policies usually attach to legal jurisdictions; outcomes can attach
   to GHSL polygons. Store many-to-many bridges with affected population and
   area shares.
5. Keep treatment jurisdictions separate from morphology. A rent-control
   ordinance applies to a municipality, state, borough, province, or regulated
   unit class; it should not be silently equated to the whole urban centre.

Builder outputs:

- `data/derived/city_universe_top1000.csv`
- `data/derived/city_universe_top1000.json`
- `data/derived/city_universe_top1000.parquet`
- `data/derived/city_crosswalks.csv`
- `data/derived/city_crosswalks.json`
- `data/derived/city_crosswalks.parquet`
- `data/manifests/fetch_run_<utc>_city_spine.yaml`

Run the builder after dropping the official GHSL UCDB R2024A CSV/XLSX/GPKG or
ZIP under `data/raw/city_level/`:

```bash
python3 scripts/build_city_spine_top1000.py --input data/raw/city_level/<ghsl_ucdb_file>
```

Recommended future file names:

- `policy_event_registry_housing.yaml`
- `ingestion_queue.yaml`

## Immediate ingest ladder

1. City universe and crosswalks: GHSL, UN WUP, OECD FUA, Eurostat Cities.
2. U.S. rent-control pilot: Zillow ZORI, Census BPS, HUD FMR/SAFMR, ACS,
   BLS CPI area rent, Eviction Lab, NYC Open Data, DataSF.
3. European pilot: Eurostat Cities, UK MHCLG live housing tables, Berlin
   Mietspiegel, Stockholm queue statistics, Spain rental reference system.
4. Local treatment registry: event-dated ordinances with coverage, exemptions,
   enforcement, and repeal/suspension fields.
5. Quality and leakage: code violations, complaints, inspections, STR
   registries, condo conversions, demolition permits, property-class changes.

## Recurring Hunt Loop

The active two-hour source hunt is governed by `data/city_level/HUNT_LOOP.md`.
Use it as the operating brief for automation runs and research swarms: append
or upgrade source records conservatively, prefer official endpoints, use
ZenRows only for blocked/JS-rendered discovery paths, and re-run validation
after every catalog or queue edit.

## Landed Panels

City spine:

```bash
python3 scripts/build_city_spine_top1000.py --input data/raw/city_level/GHS_UCDB_GLOBE_R2024A_V1_1.zip
```

U.S. city rents:

```bash
python3 scripts/build_us_zillow_city_rent_panel.py --input data/raw/city_level/City_zori_uc_sfrcondomfr_sm_month.csv
```

U.S. city permits:

```bash
python3 scripts/build_us_census_bps_city_permits_panel.py --input data/raw/city_level/BPS_Compiled_File_202604.zip
```

NYC housing quality and supply:

```bash
python3 scripts/build_nyc_open_data_housing_quality_panel.py --start-year 2007 --end-year 2026
```

NYC rent-regulation tax-benefit proxy:

```bash
python3 scripts/build_nyc_rent_regulation_tax_benefit_panel.py --start-year 2007 --end-year 2026
```

San Francisco housing quality, supply, and leakage:

```bash
python3 scripts/build_datasf_housing_quality_panel.py --start-year 1997 --end-year 2026
```

U.S. ACS place housing incidence:

```bash
CENSUS_API_KEY=<key> python3 scripts/build_us_acs_place_housing_incidence_panel.py --years 2024 --states all
```

Top-1000 rent-control readiness matrix:

```bash
python3 scripts/build_city_policy_test_readiness_matrix.py
```

Generated outputs:

- `data/derived/city_policy_test_readiness_matrix.parquet`
- `data/derived/city_policy_test_readiness_matrix.csv`
- `data/derived/city_policy_test_readiness_matrix.json`
- `data/derived/us_city_rent_panel.parquet`
- `data/derived/us_city_permits_panel.parquet`
- `data/derived/us_city_rent_control_quality_leakage_panel.parquet`
- `data/derived/us_sf_rent_control_quality_leakage_panel.parquet`
- `data/derived/nyc_rent_regulation_tax_benefit_panel.parquet`
- `engine/city_policy_test_readiness_summary.json`
- `engine/city_policy_test_readiness_summary.md`
- `data/manifests/fetch_run_2026-06-28T191500Z_city_policy_test_readiness.yaml`
- `data/manifests/fetch_run_2026-06-28T160547Z_zillow_city_rent.yaml`
- `data/manifests/fetch_run_2026-06-28T161430Z_census_bps_city_permits.yaml`
- `data/manifests/fetch_run_2026-06-28T162430Z_nyc_housing_quality_supply.yaml`
- `data/manifests/fetch_run_2026-06-28T171500Z_datasf_housing_quality_supply.yaml`
- `data/manifests/fetch_run_2026-06-28T182500Z_nyc_rent_regulation_tax_benefits.yaml`

Expected after a Census API key-backed run:

- `data/derived/us_acs_place_housing_incidence_panel.parquet`
- `data/manifests/fetch_run_<utc>_us_acs_place_housing_incidence.yaml`

## Minimum source record

Every city-level source should include:

- `source_id`
- `source_name`
- `publisher`
- `geography`
- `spatial_grain`
- `time_coverage`
- `policy_or_outcome_fields`
- `access_format`
- `source_url`
- `license_or_terms`
- `update_frequency`
- `rent_control_use`
- `second_order_layers`
- `top_1000_scalability`
- `ingestion_difficulty`
- `verification_status`

The seed inventory lives in `source_inventory.yaml`.

## Validation And Indexing

Run these after editing the catalog or queue:

```bash
python3 scripts/validate_city_level_sources.py
python3 scripts/generate_city_level_source_index.py
python3 -m pytest tests/test_city_level_sources.py tests/test_city_spine_builder.py tests/test_city_policy_test_readiness_matrix.py tests/test_us_zillow_city_rent_panel.py tests/test_us_census_bps_city_permits_panel.py tests/test_nyc_open_data_housing_quality_panel.py tests/test_nyc_rent_regulation_tax_benefit_panel.py tests/test_datasf_housing_quality_panel.py tests/test_us_acs_place_housing_incidence_panel.py
```

Generated outputs:

- `engine/city_level_source_index.json`
- `engine/city_level_source_index.md`
