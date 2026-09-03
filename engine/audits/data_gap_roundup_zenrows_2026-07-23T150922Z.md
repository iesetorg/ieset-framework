# ZenRows Data-Gap Roundup

- generated_utc: `2026-07-23T150922Z`
- manifest: `data/manifests/fetch_run_2026-07-23T150922Z.yaml`
- jobs: 8
- ok: 8
- failed: 0
- rows landed: 332,014

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `intergenerational_mobility` | 2 | 0 | 116,552 |
| `migration_labour` | 3 | 0 | 214,499 |
| `minimum_wage` | 2 | 0 | 948 |
| `renewables_lcoe` | 1 | 0 | 15 |

## Landed

- `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0` - 5,286 rows, 2016 to 2022 - OECD education-finance channel for mobility decomposition
- `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` - 111,266 rows, 2004 to 2026 - OECD housing/segregation channel for mobility decomposition
- `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0` - 2,711 rows, 2000 to 2024 - Immigrant employment rates by educational attainment
- `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0` - 14,218 rows, 2000 to 2024 - Immigrant employment/unemployment/participation rates by sex
- `oecd:OECD.ELS.IMD,DSD_MIG_F@DF_MIG_POPF,1.0` - 197,570 rows, 1995.0 to 2024.0 - Foreign-born population stocks
- `bls:OEWS_state_p10_hourly_wage_panel` - 474 rows, 2014 to 2024 - State all-occupation hourly 10th percentile wage for bite ratios
- `bls:OEWS_state_median_hourly_wage_panel` - 474 rows, 2014 to 2024 - State all-occupation hourly median wage for bite ratios
- `irena:lcoe_solar_pv` - 15 rows, 2010 to 2024 - IRENA solar PV LCOE workbook/manual-drop parser
