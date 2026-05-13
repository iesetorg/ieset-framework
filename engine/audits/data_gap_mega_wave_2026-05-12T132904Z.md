# Data-Gap Mega Wave

- generated_utc: `2026-05-12T132904Z`
- manifest: `data/manifests/fetch_run_2026-05-12T132904Z.yaml`
- jobs: 19
- ok: 8
- failed: 11
- rows landed: 1,655,191

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `bis_credit` | 2 | 1 | 31,406 |
| `bis_fx` | 1 | 0 | 1,196,431 |
| `bis_housing` | 1 | 0 | 35,388 |
| `ilo_labour` | 3 | 1 | 376,966 |
| `wdi_business` | 0 | 5 | 0 |
| `wdi_education_labour` | 0 | 3 | 0 |
| `wdi_migration` | 0 | 1 | 0 |
| `wdi_trade` | 1 | 0 | 15,000 |

## Landed

- `bis:WS_CREDIT_GAP` - 24,356 rows, 1947-Q4 to 2025-Q3 - BIS credit-to-GDP gap; crisis and credit-boom hypotheses
- `bis:WS_DSR` - 7,050 rows, 1999-Q1 to 2025-Q3 - BIS debt-service ratios
- `bis:WS_SPP` - 35,388 rows, 1927-Q1 to 2025-Q4 - BIS selected residential property prices
- `bis:WS_EER` - 1,196,431 rows, 1964-01 to 2026-05-05 - BIS effective exchange rates
- `world_bank_wdi:TX.VAL.AGRI.ZS.UN` - 15,000 rows, 1960 to 2025 - Agricultural raw materials exports share
- `ilostat:UNE_2EAP_SEX_AGE_RT_A` - 91,692 rows, 1991 to 2027 - ILO unemployment rate
- `ilostat:EAP_2WAP_SEX_AGE_RT_A` - 282,528 rows, 1990 to 2027 - ILO labour-force participation rate
- `ilostat:EAR_EHRA_SEX_NB_A` - 2,746 rows, 1990 to 2025 - ILO earnings / wage index alias

## Failed / Still Blocked

- `bis:WS_TC` - HTTPError: 404 Client Error:  for url: https://stats.bis.org/api/v2/data/dataflow/BIS/WS_TC/1.0/?format=csv
- `world_bank_wdi:IC.REC.COST` - WorldBankError: WDI error for IC.REC.COST: {'message': [{'id': '120', 'key': 'Invalid value', 'value': 'The provided parameter value is not valid'}]}
- `world_bank_wdi:IC.REC.DURS` - WorldBankError: WDI error for IC.REC.DURS: {'message': [{'id': '120', 'key': 'Invalid value', 'value': 'The provided parameter value is not valid'}]}
- `world_bank_wdi:IC.LGL.DURS` - WorldBankError: WDI error for IC.LGL.DURS: {'message': [{'id': '175', 'key': 'Invalid format', 'value': 'The indicator was not found. It may have been deleted or archived.'}]}
- `world_bank_wdi:IC.CNST.PRMT` - WorldBankError: WDI error for IC.CNST.PRMT: {'message': [{'id': '120', 'key': 'Invalid value', 'value': 'The provided parameter value is not valid'}]}
- `world_bank_wdi:IC.TAX.TOTL.CP.ZS` - WorldBankError: WDI error for IC.TAX.TOTL.CP.ZS: {'message': [{'id': '175', 'key': 'Invalid format', 'value': 'The indicator was not found. It may have been deleted or archived.'}]}
- `world_bank_wdi:SE.SEC.CMPT.LO.ZS` - HTTPError: 400 Client Error: Bad Request for url: https://api.worldbank.org/v2/country/all/indicator/SE.SEC.CMPT.LO.ZS?format=json&per_page=1000&page=1
- `world_bank_wdi:SL.TLF.ACTI.65UP.ZS` - WorldBankError: WDI error for SL.TLF.ACTI.65UP.ZS: {'message': [{'id': '120', 'key': 'Invalid value', 'value': 'The provided parameter value is not valid'}]}
- `world_bank_wdi:SL.ISV.IFRM.ZS` - WorldBankError: WDI error for SL.ISV.IFRM.ZS: {'message': [{'id': '175', 'key': 'Invalid format', 'value': 'The indicator was not found. It may have been deleted or archived.'}]}
- `world_bank_wdi:SM.EMI.TERT.ZS` - WorldBankError: WDI error for SM.EMI.TERT.ZS: {'message': [{'id': '175', 'key': 'Invalid format', 'value': 'The indicator was not found. It may have been deleted or archived.'}]}
- `ilostat:EMP_TEMP_SEX_ECO_NB_E` - HTTPError: 400 Client Error: Bad Request for url: https://rplumber.ilo.org/data/indicator/?id=EMP_TEMP_SEX_ECO_NB_E&format=.csv
