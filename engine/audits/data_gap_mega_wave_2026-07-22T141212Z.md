# Data-Gap Mega Wave

- generated_utc: `2026-07-22T141212Z`
- manifest: `data/manifests/fetch_run_2026-07-22T141212Z.yaml`
- jobs: 3
- ok: 2
- failed: 1
- rows landed: 31,604

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `bis_credit` | 2 | 1 | 31,604 |

## Landed

- `bis:WS_CREDIT_GAP` - 24,488 rows, 1947-Q4 to 2025-Q4 - BIS credit-to-GDP gap; crisis and credit-boom hypotheses
- `bis:WS_DSR` - 7,116 rows, 1999-Q1 to 2025-Q4 - BIS debt-service ratios

## Failed / Still Blocked

- `bis:WS_TC` - HTTPError: 404 Client Error:  for url: https://stats.bis.org/api/v2/data/dataflow/BIS/WS_TC/1.0/?format=csv
