# Data-Gap Mega Wave Consolidated

- generated_utc: `2026-05-12`
- purpose: record the next high-row-count trusted-source gap fill after the ZenRows/OECD/BLS/IRENA repair wave.
- note: one very large Eurostat migration pull was interrupted after it ran too long; completed vintages below were verified by reading the written parquet files.

## Landed Rows

| cluster | source | rows | period | hypothesis uses |
| --- | --- | ---: | --- | --- |
| BIS credit | `bis:WS_CREDIT_GAP` | 24,356 | 1947-Q4-2025-Q3 | credit booms, crisis predictors, Austrian credit-cycle tests |
| BIS credit | `bis:WS_DSR` | 7,050 | 1999-Q1-2025-Q3 | household debt, balance-sheet recession, financial fragility |
| BIS housing | `bis:WS_SPP` | 35,388 | 1927-Q1-2025-Q4 | house prices, mortgage cycles, housing-credit reversals |
| BIS FX | `bis:WS_EER` | 1,196,431 | 1964-01-2026-05-05 | REER/NEER controls for trade, crisis, and competitiveness tests |
| WDI trade | `world_bank_wdi:TX.VAL.AGRI.ZS.UN` | 15,000 | 1960-2025 | agricultural export diversification |
| ILO labour | `ilostat:UNE_2EAP_SEX_AGE_RT_A` | 91,692 | 1991-2027 | unemployment controls/outcomes |
| ILO labour | `ilostat:EAP_2WAP_SEX_AGE_RT_A` | 282,528 | 1990-2027 | labour-force participation and demographic labour tests |
| ILO wages | `ilostat:EAR_EHRA_SEX_NB_A` | 2,746 | 1990-2025 | wage-index fallback for labour and migration tests |
| OECD social | `oecd:DSD_SOCX@DF_SOCX_AGG` | 3,060,473 | 1980-2024 | welfare scale, stabilisers, pension/welfare architecture |
| OECD labour | `oecd:EPL_OV` | 1,123 | 1985-2019 | labour-market flexibility, EPL, ALMP complementarity |
| OECD labour | `oecd:DSD_LMS_low_education_unemployment_rate` | 926,337 | 1981-2024 | minimum-wage low-education outcomes, labour-market distribution |
| OECD productivity | `oecd:DSD_PDB` | 1,734,430 | 1950-2025 | productivity, TFP, frontier growth, wage/productivity decomposition |
| Eurostat macro | `eurostat:nama_10_gdp` | 1,100,189 | 1975-2025 | EU national accounts, austerity, growth, fiscal-policy cases |
| Eurostat sectoral | `eurostat:nama_10_a10` | 869,177 | 1975-2025 | sectoral structure, services, industry, productivity decompositions |
| Eurostat labour | `eurostat:une_rt_a` | 39,669 | 2003-2025 | EU unemployment outcomes |
| Eurostat labour | `eurostat:lfsa_egan` | 414,005 | 1995-2025 | EU employment by activity |
| Eurostat distribution | `eurostat:ilc_di12` | 870 | 2014-2025 | EU income distribution |
| Eurostat energy | `eurostat:nrg_pc_205` | 79,560 | 2007-S1-2025-S2 | industrial electricity prices, nuclear/energy-price tests |
| BLS QCEW | `bls:QCEW_county_NAICS722_employment_panel` | 35,770 | 2014-2024 | county food-service employment for minimum-wage designs |
| BLS QCEW | `bls:QCEW_state_NAICS722_employment_panel` | 561 | 2014-2024 | state food-service employment for minimum-wage designs |

Total landed in this consolidated wave: 9,917,355 rows.

## Important Partial Failures

- `bis:WS_TC`: BIS returned 404 for the local dataflow id. Use catalogue discovery; likely the total-credit dataflow id/key has changed.
- Several WDI Doing Business indicators are archived/deleted in the public WDI API. Treat these as source-id repair tasks, not source-quality failures.
- `ilostat:EMP_TEMP_SEX_ECO_NB_E`: ILO returned 400 for the local indicator id. Needs indicator catalogue lookup.
- OECD ALMP, pensions, child poverty, house prices, HFCE, and government expenditure returned 404 under the current shortcut IDs. The source is still valid; the local OECD shortcut map needs refreshed catalogue IDs.
- `eurostat:migr_imm1ctz` was interrupted because the bulk payload ran too long. Rerun with filters or a streaming/cache-aware fetcher.
- BLS LAU state unemployment and employment-population panels hit the unauthenticated public API daily threshold. Retry after reset or with a BLS API key.
- `bls:QCEW_state_total_employment_panel` was stopped after running too long; use a narrower public-file parser or derive state total from a lighter QCEW all-industry endpoint.

## Immediate Unlocks

1. Credit-cycle and financial-fragility hypotheses can now use BIS `WS_CREDIT_GAP`, `WS_DSR`, `WS_SPP`, and `WS_EER`.
2. Welfare-scale and automatic-stabiliser hypotheses now have a large OECD SOCX aggregate vintage.
3. Minimum-wage and labour-distribution hypotheses now have OECD low-education unemployment plus BLS QCEW food-service state/county panels.
4. Productivity and frontier-growth hypotheses now have OECD PDB and Eurostat sectoral national-accounts underlays.
5. Nuclear/energy price hypotheses now have a fresh Eurostat electricity-price vintage to complement IRENA and any future ENTSO-E/IEA pulls.

## Follow-Up Fetch Repairs

1. Refresh OECD shortcut IDs via the dataflow catalogue for ALMP, pensions, child poverty, house prices, HFCE, and GFS/government expenditure.
2. Add a World Bank archived Doing Business source or replacement B-READY/Enterprise Surveys source for insolvency, contracts, construction permits, and tax burden.
3. Add BLS API key support in the local environment or switch LAU state panels to downloadable flat files to avoid daily public limits.
4. Rerun Eurostat migration with filters by geo/time/citizenship instead of full unfiltered bulk.
5. Add a BIS catalogue probe for total credit if `WS_TC` has moved or requires a key.
