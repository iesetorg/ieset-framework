# State-Level Data Expansion

This directory tracks the admin1/state-level data program opened on
2026-06-29. It exists to close the gap between country-level panels and the new
top-1000 city layer: many treatments live at the state, province, canton,
Land, territory, or region level, and country-year proxies wash out that
variation.

## Canonical State Key

Use a separate state identity spine before writing broad fetchers:

1. Prefer `geoboundaries_admin1` as the global boundary anchor once the ADM1
   files are fetched or dropped.
2. Preserve `ISO3`, native admin1 codes, ISO-3166-2 where available, and
   publisher IDs such as U.S. FIPS, NUTS, OECD TL2/TL3, StatCan province,
   IBGE UF, INEGI state, ABS STE, and India state/UT codes.
3. Separate legal policy jurisdictions from statistical regions. NUTS, TL2,
   and local authority geographies can support outcomes without being legal
   treatment units.
4. Store many-to-many crosswalks when a legal state/province does not map
   cleanly to a statistical region.
5. Never collapse state/province policy events into country-year treatments.

Builder outputs:

- `data/derived/state_universe_admin1.csv`
- `data/derived/state_universe_admin1.json`
- `data/derived/state_universe_admin1.parquet`
- `data/derived/state_crosswalks.csv`
- `data/derived/state_crosswalks.json`
- `data/derived/state_crosswalks.parquet`
- `data/manifests/fetch_run_<utc>_state_spine.yaml`

Initial U.S. v0 builder:

```bash
python3 scripts/build_state_spine_admin1.py
```

That v0 is intentionally conservative: it mints U.S. state-equivalent IDs from
the existing USDOL state minimum-wage vintage, then crosswalks them to
ISO-3166-2-style IDs, state abbreviations, and FIPS codes. Global ADM1
expansion should extend the builder with geoBoundaries/GADM/ISO inputs.

## Immediate Ingest Ladder

1. State spine and crosswalks: geoBoundaries ADM1, GADM ADM1, ISO-3166-2,
   Natural Earth admin1, plus local national codes.
2. U.S. state labor pilot: USDOL minimum wage, BLS LAU, BLS OEWS, BLS QCEW,
   derived bite ratios, Census population/ACS controls.
3. U.S. housing/fiscal controls: Census BPS state permits, BEA state accounts,
   NASBO spending, EIA SEDS, CDC WONDER, NCES, FBI CDE.
4. OECD/Europe: OECD regional statistics, Eurostat NUTS, Germany Laender,
   Swiss cantons, UK nations/regions, Canadian provinces.
5. Large federal systems: Brazil UFs, Mexico states, India states/UTs, China
   provinces, South Africa provinces, Australia states/territories.
6. State policy-event registry: event dates, treatment intensity, exemptions,
   enforcement body, repeal/sunset, and official legal citations.

## Recurring Hunt Loop

The active source hunt is governed by `data/state_level/HUNT_LOOP.md`. Use it
for research swarms: append or upgrade source records conservatively, prefer
official endpoints, keep legal treatment jurisdictions separate from
statistical regions, and rerun validation after every catalog or queue edit.

## Landed Panels

State spine:

```bash
python3 scripts/build_state_spine_admin1.py
```

Existing U.S. state/subnational vintages already on disk:

- `data/vintages/usdol/state_minimum_wage_history@2026-05-04T145319Z.parquet`
- `data/vintages/bls/LAU_state_unemployment_rate_panel@2026-05-05T204700Z.parquet`
- `data/vintages/bls/LAU_state_employment_population_ratio_panel@2026-05-14T110716Z.parquet`
- `data/vintages/bls/OEWS_state_median_hourly_wage_panel@2026-05-12T125636Z.parquet`
- `data/vintages/bls/OEWS_state_p10_hourly_wage_panel@2026-05-12T125547Z.parquet`
- `data/vintages/bls/QCEW_state_total_employment_panel@2026-05-05T204746Z.parquet`
- `data/vintages/bls/QCEW_state_NAICS722_employment_panel@2026-05-12T140559Z.parquet`
- `data/vintages/derived/minimum_wage_bite_ratio_subnational_panel@2026-05-14T111058Z.parquet`

## Validation And Indexing

Run these after editing the catalog or queue:

```bash
python3 scripts/validate_state_level_sources.py
python3 scripts/generate_state_level_source_index.py
python3 -m pytest tests/test_state_level_sources.py
```

When the state spine builder changes, also run:

```bash
python3 -m pytest tests/test_state_spine_builder.py
```

## Minimum Source Record

Every state-level source should include:

- `source_id`
- `source_name`
- `publisher`
- `geography`
- `spatial_grain`
- `time_coverage`
- `policy_or_outcome_fields`
- `policy_domains`
- `access_format`
- `source_url`
- `license_or_terms`
- `update_frequency`
- `state_level_use`
- `second_order_layers`
- `admin1_scalability`
- `ingestion_difficulty`
- `verification_status`

The seed inventory lives in `source_inventory.yaml`.
