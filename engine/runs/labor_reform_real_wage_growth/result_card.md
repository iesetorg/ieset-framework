# Result card - labor_reform_real_wage_growth

**Verdict:** PARTIAL - exact wage/productivity proxy does not clear the positive/significant wage gate

## Pre-registration
- **Claim:** Higher market-compatible regulatory quality predicts stronger long-run real wage and income proxies.
- **Falsification rule:** SUPPORTED if the treatment coefficient has the pre-registered sign at p<0.10. REFUTED if the opposite sign is significant at p<0.10. Otherwise PARTIAL.
- **Falsification test:** panel_fe_labor_reform_real_wage_growth

## Method
Country-year FE panel using OECD PDB labour compensation per hour deflated by WDI CPI as the real-wage proxy, with lagged WGI regulatory quality and rule-of-law/income controls.

## Estimates
### real_comp_hour_growth_proxy
- Sample: n=448, countries=21, years=1998-2023
- R-squared: 0.447
- `regulatory_quality_lag`: beta=+0.5106, se=0.9967, p=0.6141
- `log_gdp_pc`: beta=+2.559, se=2.068, p=0.2302
- `rule_of_law`: beta=-2.979, se=1.644, p=0.08497

### labour_productivity_growth
- Sample: n=434, countries=20, years=1998-2023
- R-squared: 0.320
- `regulatory_quality_lag`: beta=-0.02954, se=0.5952, p=0.9609
- `log_gdp_pc`: beta=-1.925, se=1.107, p=0.09819
- `rule_of_law`: beta=-1.472, se=0.7916, p=0.07852

## Interpretation
This replaces the prior GDP-per-capita proxy with a closer compensation-per-hour proxy while preserving the registered direction test as research-only.

## Variables Loaded
- `real_comp_hour_growth_proxy` (outcome_proxy): oecd_pdb:LCHRS_GY total economy minus WDI CPI inflation
- `labour_productivity_growth` (outcome): oecd_pdb:GDPHRS_GY total economy
- `regulatory_quality_lag` (treatment): wgi:GOV_WGI_RQ.EST lagged one year
- `log_gdp_pc, rule_of_law` (controls): WDI and WGI

## Missing Or Proxied
- `real wage growth` (exact_outcome): OECD average-wage/median-wage real series not local for broad sample
- `labour-market reform episodes` (exact_treatment): policy event panel not local

## Source Paths
- `OECD Productivity Database` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- `WDI CPI inflation` -> `data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-04-30T135619Z.parquet`
- `World Governance Indicators regulatory quality` -> `data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet`
- `World Governance Indicators rule of law` -> `data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet`
- `WDI real GDP per capita` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet`

## Caveats
- The wage outcome is labour compensation per hour deflated by CPI, not a worker-level real wage series.
- Regulatory quality is a broad institutional proxy, not a specific labour reform treatment.
