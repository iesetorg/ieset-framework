# Daily Rate-Limited Data Backfill

- generated_utc: `2026-05-19T231640Z`
- manifest: `data/manifests/fetch_run_2026-05-19T231640Z.yaml`
- ok: 0
- failed: 1
- rows landed: 0

## Landed


## Failed / Still Blocked

- `bls:QCEW_state_total_employment_panel` — ConnectionError: HTTPSConnectionPool(host='data.bls.gov', port=443): Max retries exceeded with url: /cew/data/api/2024/a/industry/10.csv (Caused by NameResolutionError("HTTPSConnection(host='data.bls.gov', port=443): Failed to resolve 'data.bls.gov' ([Errno 8] nodename nor servname provided, or not known)"))

## Run Settings

- `BLS_API_KEY`: `unset`
- `BLS_LAU_START_YEAR`: `1990`
- `BLS_LAU_END_YEAR`: `2024`
- `BLS_QCEW_START_YEAR`: `2024`
- `BLS_QCEW_END_YEAR`: `2024`
