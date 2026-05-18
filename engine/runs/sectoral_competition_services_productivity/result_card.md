# Result card - sectoral_competition_services_productivity

**Verdict:** PARTIAL - proxy horse-race does not clear the registered positive/significant services-productivity gate

## Pre-registration
- **Claim:** Among high-income economies 1990-2020, services-sector competition - measured by low barriers to entry, low incumbent-protection scores, and high churn in retail, transport, communications, and professional services - predicts long-run prosperity (real GDP per capita growth and labour-productivity growth) better than manufacturing-specific industrial policy spending. The pre- registered claim is that, in a horse-race regression, the coefficient on services-sector competition is larger in absolute t-statistic than the coefficient on manufacturing industrial- policy spending, and that countries in the top tercile of services competition show at least 0.3 percentage points higher annual labour-productivity growth than countries in the bottom tercile.

- **Falsification rule:** Not supported if (a) the services-competition coefficient is not positive and significant at p<0.05 on productivity growth, OR (b) in the horse-race the manufacturing-industrial-policy coefficient has a larger absolute t-statistic than services competition, OR (c) the top-tercile vs bottom-tercile productivity growth gap is below 0.15 pp/year. A manufacturing-first / industrial-policy reading wins cleanly if manufacturing policy outperforms services competition in the horse-race.

- **Falsification test:** panel_fe_horserace_services_competition_vs_manufacturing_policy

## Method
Cross-sectional OECD 2023 PMR services-competition proxy against 2019-2024 PDB services labour-productivity growth; HC1 robust OLS with initial income and manufacturing-share controls.

## Estimates
### services_productivity_growth_2019_2024
- Sample: n=30, countries=30, years=2023-2023
- R-squared: 0.090
- `services_competition_index`: beta=-0.1182, se=0.2088, p=0.5765
- `state_involvement_z`: beta=+0.1418, se=0.2405, p=0.5609
- `log_gdp_pc_2018`: beta=-0.1318, se=0.29, p=0.6535
- `manufacturing_share_2018`: beta=-0.008109, se=0.02637, p=0.761
- top_minus_bottom_services_competition_gap_pp_per_year: -0.9509
- top_tercile_mean: 1.2219
- bottom_tercile_mean: 2.1728

## Interpretation
The local OECD proxy does not provide a clean services-competition win over state-involvement controls; keep the artifact research-only until longer PMR/STAN coverage and direct industrial-policy spending are loaded.

## Variables Loaded
- `services_productivity_growth_2019_2024` (outcome): oecd_pdb:GVAHRS_GY_L averaged over G,H,J,M_N
- `services_competition_index` (treatment): inverted z-score of OECD PMR PROFSERV, BARRIER_ENTRY, NETWORK_SECTORS
- `state_involvement_z` (horse_race_proxy): oecd_pmr:STATE_INVOL
- `log_gdp_pc_2018, manufacturing_share_2018` (controls): world_bank_wdi

## Missing Or Proxied
- `manufacturing_industrial_policy_spending` (exact_treatment): constructed state-aid/subsidy/directed-credit series not local
- `services-sector churn` (exact_treatment): firm entry/exit microdata not local

## Source Paths
- `OECD Productivity Database` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- `OECD product market regulation` -> `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet`
- `OECD PMR barriers to entry` -> `data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet`
- `OECD PMR network-sector regulation` -> `data/vintages/oecd_pmr/NETWORK_SECTORS@2026-05-02T220000Z.parquet`
- `OECD PMR state involvement` -> `data/vintages/oecd_pmr/STATE_INVOL@2026-05-02T220000Z.parquet`
- `WDI real GDP per capita` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet`
- `WDI manufacturing share` -> `data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet`

## Caveats
- PMR coverage is limited to 2018 and 2023, so the test is a short-window proxy rather than a 1990-2020 panel.
- Services productivity uses PDB GVA per hour for retail/transport/information/professional activities as the local STAN-equivalent proxy.
