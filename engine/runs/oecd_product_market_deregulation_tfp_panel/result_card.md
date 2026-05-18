# Result card - oecd_product_market_deregulation_tfp_panel

**Verdict:** PARTIAL - short-window PMR decline proxy does not clear both positive/significant productivity gates

## Pre-registration
- **Claim:** In OECD and accession-country panels 1998-2019, reductions in the OECD PMR overall product-market-regulation index predict higher subsequent TFP growth. The directional claim is that a one-standard-deviation reduction in PMR predicts at least 0.2 percentage points higher annual TFP growth over the following 5-year window, controlling for initial TFP level, R&D intensity, and human capital.

- **Falsification rule:** SUPPORTED if beta1 (PMR, inverted) is positive and significant at p<0.05 for both TFP growth and labour productivity growth. PARTIAL if positive and significant for TFP but not labour productivity. REFUTED if beta1 is negative and significant at p<0.05. INFORMATIVE: the result should survive excluding the UK and New Zealand (dominant deregulation cases); if not, it is a two-country story.

- **Falsification test:** panel_fe_pmr_deregulation_tfp_oecd

## Method
OECD cross-section replacing the infeasible two-year TWFE PMR panel with PMR decline from 2018 to 2023 and 2019-2024 PDB MFP/labour-productivity growth.

## Estimates
### mfp_growth_2019_2024
- Sample: n=18, countries=18, years=2024-2024
- R-squared: 0.189
- `pmr_decline_z`: beta=+0.1544, se=0.6002, p=0.8011
- `log_tfp_2018`: beta=-4.98, se=26.3, p=0.8528
- `hc`: beta=+0.8145, se=1.087, p=0.4672
- `trade_openness_2018`: beta=+0.005604, se=0.006762, p=0.4222

### lp_growth_2019_2024
- Sample: n=18, countries=18, years=2024-2024
- R-squared: 0.501
- `pmr_decline_z`: beta=+0.1618, se=0.4093, p=0.699
- `log_tfp_2018`: beta=+16, se=18.08, p=0.3922
- `hc`: beta=+1.663, se=0.8328, p=0.06726
- `trade_openness_2018`: beta=+0.0003136, se=0.004969, p=0.9506

## Interpretation
The repaired local design is more informative than the failed FE rerun, but remains a short-window proxy around the 2018/2023 PMR vintages.

## Variables Loaded
- `mfp_growth_2019_2024` (outcome): oecd_pdb:MFPH_GY_LR total economy
- `lp_growth_2019_2024` (outcome): oecd_pdb:GDPHRS_GY_L total economy
- `pmr_decline_2018_2023` (treatment): decline in OECD PMR overall index
- `log_tfp_2018, hc, trade_openness_2018` (controls): PWT and WDI

## Missing Or Proxied
- `1998-2019 PMR panel` (exact_design): local PMR vintage has only 2018 and 2023
- `R&D intensity` (control): not used because PDB R&D extraction is sparse in this window

## Source Paths
- `OECD Productivity Database` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- `OECD product market regulation` -> `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet`
- `Penn World Table full panel` -> `data/vintages/pwt/pwt_full@2026-05-05T195237Z.parquet`
- `WDI trade openness` -> `data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet`

## Caveats
- This repairs the previous no-within-country-variation failure by using the pre-registered PMR-change exposure as a cross-section.
- PDB MFP coverage is used instead of PWT TFP because the local PWT vintage ends before the 2023 PMR endpoint.
