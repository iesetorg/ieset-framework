# ZenRows Data-Gap Roundup

- generated_utc: `2026-07-19T124533Z`
- manifest: `data/manifests/fetch_run_2026-07-19T124533Z.yaml`
- jobs: 8
- ok: 6
- failed: 2
- rows landed: 112,252

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `intergenerational_mobility` | 1 | 0 | 111,266 |
| `minimum_wage` | 2 | 0 | 948 |
| `occupational_licensing` | 0 | 2 | 0 |
| `renewables_lcoe` | 2 | 0 | 30 |
| `wealth_tax` | 1 | 0 | 8 |

## Landed

- `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` - 111,266 rows, 2004 to 2026 - OECD housing/segregation channel for mobility decomposition
- `bls:OEWS_state_p10_hourly_wage_panel` - 474 rows, 2014 to 2024 - State all-occupation hourly 10th percentile wage for bite ratios
- `bls:OEWS_state_median_hourly_wage_panel` - 474 rows, 2014 to 2024 - State all-occupation hourly median wage for bite ratios
- `irena:lcoe_solar_pv` - 15 rows, 2010 to 2024 - IRENA solar PV LCOE workbook/manual-drop parser
- `irena:lcoe_wind_onshore` - 15 rows, 2010 to 2024 - IRENA onshore wind LCOE workbook/manual-drop parser
- `wealth_tax_manual:revenue_forecast_realized` - 8 rows, 2015 to 2023 - Manual realized-vs-forecast wealth-tax panel

## Failed / Still Blocked

- `kleiner_krueger:kk_state_licensing_share_workforce` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: /Users/localllm/IESET/data/manual/kleiner_krueger
- `kleiner_krueger:kk_state_2015_share_pct` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: /Users/localllm/IESET/data/manual/kleiner_krueger
