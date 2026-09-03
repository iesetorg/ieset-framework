# Data-Gap Mega Wave

- generated_utc: `2026-07-23T152624Z`
- manifest: `data/manifests/fetch_run_2026-07-23T152624Z.yaml`
- jobs: 4
- ok: 3
- failed: 1
- rows landed: 377,002

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `ilo_labour` | 3 | 1 | 377,002 |

## Landed

- `ilostat:UNE_2EAP_SEX_AGE_RT_A` - 91,692 rows, 1991 to 2027 - ILO unemployment rate
- `ilostat:EAP_2WAP_SEX_AGE_RT_A` - 282,528 rows, 1990 to 2027 - ILO labour-force participation rate
- `ilostat:EAR_EHRA_SEX_NB_A` - 2,782 rows, 1990 to 2026 - ILO earnings / wage index alias

## Failed / Still Blocked

- `ilostat:EMP_TEMP_SEX_ECO_NB_E` - HTTPError: 400 Client Error: Bad Request for url: https://rplumber.ilo.org/data/indicator/?id=EMP_TEMP_SEX_ECO_NB_E&format=.csv
