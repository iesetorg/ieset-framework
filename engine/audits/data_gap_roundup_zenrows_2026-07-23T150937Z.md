# ZenRows Data-Gap Roundup

- generated_utc: `2026-07-23T150937Z`
- manifest: `data/manifests/fetch_run_2026-07-23T150937Z.yaml`
- jobs: 4
- ok: 2
- failed: 2
- rows landed: 23

## Cluster Summary

| cluster | ok | failed | rows |
| --- | ---: | ---: | ---: |
| `occupational_licensing` | 0 | 2 | 0 |
| `renewables_lcoe` | 1 | 0 | 15 |
| `wealth_tax` | 1 | 0 | 8 |

## Landed

- `irena:lcoe_wind_onshore` - 15 rows, 2010 to 2024 - IRENA onshore wind LCOE workbook/manual-drop parser
- `wealth_tax_manual:revenue_forecast_realized` - 8 rows, 2015 to 2023 - Manual realized-vs-forecast wealth-tax panel

## Failed / Still Blocked

- `kleiner_krueger:kk_state_licensing_share_workforce` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: /Users/localllm/IESET/data/manual/kleiner_krueger
- `kleiner_krueger:kk_state_2015_share_pct` - ManualDropError: No manual-drop dir for 'kleiner_krueger'. See module docstring for steps; expected directory: /Users/localllm/IESET/data/manual/kleiner_krueger
