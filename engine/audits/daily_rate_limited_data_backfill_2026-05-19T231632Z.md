# Daily Rate-Limited Data Backfill

- generated_utc: `2026-05-19T231632Z`
- manifest: `data/manifests/fetch_run_2026-05-19T231632Z.yaml`
- ok: 0
- failed: 1
- rows landed: 0

## Landed


## Failed / Still Blocked

- `bls:LAU_state_employment_population_ratio_panel` — ConnectionError: HTTPSConnectionPool(host='api.bls.gov', port=443): Max retries exceeded with url: /publicAPI/v2/timeseries/data/ (Caused by NameResolutionError("HTTPSConnection(host='api.bls.gov', port=443): Failed to resolve 'api.bls.gov' ([Errno 8] nodename nor servname provided, or not known)"))

## Run Settings

- `BLS_API_KEY`: `unset`
- `BLS_LAU_START_YEAR`: `1990`
- `BLS_LAU_END_YEAR`: `2025`
- `BLS_QCEW_START_YEAR`: `2019`
- `BLS_QCEW_END_YEAR`: `2024`
