# ZenRows Data-Gap Roundup

- generated_utc: `2026-05-12T120817Z`
- manifest: `data/manifests/fetch_run_2026-05-12T120817Z.yaml`
- jobs: 8
- ok: 3
- failed: 5
- rows landed: 214,499

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `migration_labour` | 3 | 0 | 214,499 |
| `occupational_licensing` | 0 | 2 | 0 |
| `renewables_lcoe` | 0 | 2 | 0 |
| `wealth_tax` | 0 | 1 | 0 |

## Landed

- `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0` - 2,711 rows, 2000 to 2024 - Immigrant employment rates by educational attainment
- `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0` - 14,218 rows, 2000 to 2024 - Immigrant employment/unemployment/participation rates by sex
- `oecd:OECD.ELS.IMD,DSD_MIG_F@DF_MIG_POPF,1.0` - 197,570 rows, 1995.0 to 2024.0 - Foreign-born population stocks

## Failed / Still Blocked

- `kleiner_krueger:kk_state_licensing_share_workforce` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: ./data/manual/kleiner_krueger
- `kleiner_krueger:kk_state_2015_share_pct` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: ./data/manual/kleiner_krueger
- `irena:lcoe_solar_pv` - IrenaError: No files (xlsx, xls, csv) in data/manual/irena. Drop the latest publisher file there.
Drop the latest IRENA Renewable Power Generation Costs or Renewable Capacity Statistics file into data/manual/irena/.
- `irena:lcoe_wind_onshore` - IrenaError: No files (xlsx, xls, csv) in data/manual/irena. Drop the latest publisher file there.
Drop the latest IRENA Renewable Power Generation Costs or Renewable Capacity Statistics file into data/manual/irena/.
- `wealth_tax_manual:revenue_forecast_realized` - WealthTaxManualError: missing data/manual/wealth_tax/revenue_forecast_realized.csv; copy the template and fill sourced rows
