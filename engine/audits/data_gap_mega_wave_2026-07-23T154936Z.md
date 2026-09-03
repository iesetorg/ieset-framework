# Data-Gap Mega Wave

- generated_utc: `2026-07-23T154936Z`
- manifest: `data/manifests/fetch_run_2026-07-23T154936Z.yaml`
- jobs: 13
- ok: 9
- failed: 4
- rows landed: 2,092,476

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `bls_state_county` | 4 | 1 | 58,312 |
| `eurostat_distribution` | 1 | 0 | 870 |
| `eurostat_energy` | 1 | 0 | 79,632 |
| `eurostat_macro` | 2 | 0 | 1,952,307 |
| `oecd_distribution` | 0 | 1 | 0 |
| `oecd_housing` | 0 | 1 | 0 |
| `oecd_labour` | 1 | 1 | 1,355 |

## Landed

- `oecd:OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0` - 1,355 rows, 1985 to 2025 - OECD employment-protection legislation
- `eurostat:nama_10_gdp` - 1,093,133 rows, 1975 to 2025 - Eurostat national accounts GDP
- `eurostat:nama_10_a10` - 859,174 rows, 1975 to 2025 - Eurostat sectoral national accounts
- `eurostat:ilc_di12` - 870 rows, 2014 to 2025 - Eurostat income distribution
- `eurostat:nrg_pc_205` - 79,632 rows, 2007-S1 to 2025-S2 - Eurostat electricity prices
- `bls:LAU_state_unemployment_rate_panel` - 21,420 rows, 1990 to 2024 - BLS state unemployment rates
- `bls:QCEW_state_total_employment_panel` - 561 rows, 2014 to 2024 - BLS QCEW state total employment
- `bls:QCEW_state_NAICS722_employment_panel` - 561 rows, 2014 to 2024 - BLS QCEW state food-service employment
- `bls:QCEW_county_NAICS722_employment_panel` - 35,770 rows, 2014 to 2024 - BLS QCEW county food-service employment

## Failed / Still Blocked

- `oecd:DSD_LMS_low_education_unemployment_rate` - OecdError: OECD 404 for DSD_LMS_low_education_unemployment_rate (resolved='OECD.EDU.IMEP,DSD_EAG_LSO_EA@DF_LSO_NEAC_UNEMP,1.0') key='' — check dataflow id
- `oecd:DSD_IDD@DF_CHILD_POV` - OecdError: OECD 404 for DSD_IDD@DF_CHILD_POV (resolved='OECD.WISE.INE,DSD_WISE_IDD@DF_CHILD_POV,1.0') key='' — check dataflow id
- `oecd:HOUSE_PRICES` - OecdError: OECD 404 for HOUSE_PRICES (resolved='OECD.SDD.PIN,DSD_RHPI@DF_RHPI,1.0') key='' — check dataflow id
- `bls:LAU_state_employment_population_ratio_panel` - BlsError: BLS batch failed: REQUEST_NOT_PROCESSED — ['Request could not be serviced, as the daily threshold for total number of requests allocated to the user with registration key  has been reached.']
