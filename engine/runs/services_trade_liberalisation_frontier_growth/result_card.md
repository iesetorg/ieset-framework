# Result card - services_trade_liberalisation_frontier_growth

**Verdict:** INCONCLUSIVE_DATA_PENDING - local PMR trade-barrier proxy does not settle the STRI/services-TFP hypothesis

## Pre-registration
- **Claim:** Services trade liberalisation predicts stronger total factor productivity growth in high-income frontier economies after 1990 than goods-sector industrial policy does. The directional claim is that a one-standard- deviation reduction in services trade restrictiveness (OECD STRI or equivalent) predicts larger TFP growth gains in the subsequent decade than a one-standard-deviation increase in goods-sector subsidy or tariff-protection intensity, in an OECD and high-income panel 1990-2020.

- **Falsification rule:** SUPPORTED if beta1 (services liberalisation) is positive and significant at p<0.10 while beta2 (goods industrial policy) is insignificant or negative, AND |beta1| > |beta2|. PARTIAL if both are positive and significant but beta1 > beta2. REFUTED if beta1 is negative and significant or if beta2 is positive and significantly larger than beta1. INFORMATIVE: the result should survive excluding the United States; if not, it is a US deregulation story rather than a general services-liberalisation effect.

- **Falsification test:** panel_fe_services_vs_goods_industrial_policy_tfp_frontier

## Method
Cross-sectional OECD proxy: decline in PMR barriers to trade/investment from 2018 to 2023 predicts 2019-2024 PDB services MFP growth, compared with state-involvement/tariff goods-policy proxy.

## Estimates
### services_mfp_growth_2019_2024
- Sample: n=17, countries=17, years=2024-2024
- R-squared: 0.142
- `services_trade_liberalisation_z`: beta=+0.8831, se=0.7896, p=0.2853
- `goods_policy_intensity_z`: beta=+0.2103, se=0.2604, p=0.435
- `log_gdp_pc_2018`: beta=-0.07274, se=0.9049, p=0.9373
- `log_tfp_2018`: beta=+18.49, se=26.54, p=0.4992

## Interpretation
The available local data are useful for triage but not dispositive: they replace STRI and goods subsidies with PMR trade/tariff/state-involvement proxies.

## Variables Loaded
- `services_mfp_growth_2019_2024` (outcome_proxy): oecd_pdb:MFPH_GY_LR averaged over G,H,J,M_N
- `services_trade_liberalisation_2018_2023` (treatment_proxy): decline in oecd_pmr:BARRIER_TRADE
- `goods_policy_intensity_z` (horse_race_proxy): oecd_pmr:STATE_INVOL and TARIFFS
- `log_gdp_pc_2018, log_tfp_2018` (controls): WDI and PWT

## Missing Or Proxied
- `OECD STRI overall/services-sector index` (exact_treatment): not local
- `EU KLEMS/OECD STAN sectoral TFP for services` (exact_outcome): not local beyond PDB MFP proxy
- `goods-sector subsidy intensity` (exact_horse_race): CRDF/ITC/WITS subsidy panel not local

## Source Paths
- `OECD Productivity Database` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- `OECD PMR barriers to trade/investment` -> `data/vintages/oecd_pmr/BARRIER_TRADE@2026-05-02T220000Z.parquet`
- `OECD PMR state involvement` -> `data/vintages/oecd_pmr/STATE_INVOL@2026-05-02T220000Z.parquet`
- `OECD PMR tariffs` -> `data/vintages/oecd_pmr/TARIFFS@2026-05-02T220000Z.parquet`
- `Penn World Table full panel` -> `data/vintages/pwt/pwt_full@2026-05-05T195237Z.parquet`
- `WDI real GDP per capita` -> `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-04-30T113730Z.parquet`

## Caveats
- PMR barriers to trade are a broad trade/investment-barrier proxy, not the OECD STRI.
- Only the 2018-2023 PMR change is local, so this is a short-window screen.
