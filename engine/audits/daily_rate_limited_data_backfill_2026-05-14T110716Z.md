# Daily Rate-Limited Data Backfill

- generated_utc: `2026-05-14T110716Z`
- manifest: `data/manifests/fetch_run_2026-05-14T110816Z.yaml`
- ok: 2
- failed: 1
- rows landed: 21,522

## Landed

- `bls:LAU_state_employment_population_ratio_panel` — 21,420 rows, 1990 to 2024 — BLS LAU state monthly employment-population ratio panel
  - source_url: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
  - methodology_url: `https://www.bls.gov/lau/`
  - vintage: `data/vintages/bls/LAU_state_employment_population_ratio_panel@2026-05-14T110716Z.parquet`
- `bls:QCEW_state_total_employment_panel` — 102 rows, 2023 to 2024 — BLS QCEW state total employment panel (bounded year window)
  - source_url: `https://data.bls.gov/cew/data/api/{year}/a/industry/10.csv`
  - methodology_url: `https://www.bls.gov/cew/downloadable-data-files.htm`
  - vintage: `data/vintages/bls/QCEW_state_total_employment_panel@2026-05-14T110759Z.parquet`

## Failed / Still Blocked

- `bls:LAU_state_unemployment_rate_panel` — BlsError: BLS batch failed: REQUEST_NOT_PROCESSED — ['Request could not be serviced, as the daily threshold for total number of requests allocated to the user with registration key  has been reached.']

## Run Settings

- `BLS_API_KEY`: `unset`
- `BLS_LAU_START_YEAR`: `1990`
- `BLS_LAU_END_YEAR`: `2024`
- `BLS_QCEW_START_YEAR`: `2023`
- `BLS_QCEW_END_YEAR`: `2024`
