# Data-Gap Mega Wave

- generated_utc: `2026-07-23T152609Z`
- manifest: `data/manifests/fetch_run_2026-07-23T152609Z.yaml`
- jobs: 2
- ok: 1
- failed: 1
- rows landed: 5,000

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `wdi_migration` | 0 | 1 | 0 |
| `wdi_trade` | 1 | 0 | 5,000 |

## Landed

- `world_bank_wdi:TX.VAL.AGRI.ZS.UN` - 5,000 rows, 1960 to 2025 - Agricultural raw materials exports share

## Failed / Still Blocked

- `world_bank_wdi:SM.EMI.TERT.ZS` - WorldBankError: WDI error for SM.EMI.TERT.ZS: {'message': [{'id': '175', 'key': 'Invalid format', 'value': 'The indicator was not found. It may have been deleted or archived.'}]}
