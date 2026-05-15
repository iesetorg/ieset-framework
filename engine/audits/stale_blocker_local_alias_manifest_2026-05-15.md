# Stale Blocker Local Alias Manifest - 2026-05-15

Scope: derived audit-only manifest for Batch A3 stale blockers. No network fetches were used and no hypothesis, position, runner, run-directory, or source data files were edited.

## Safe Local Alias Candidates

| Blocker token seen in stale run | Local file/source now present | Safe repair action | Unlocks |
| --- | --- | --- | --- |
| `derived:minimum_wage_bite_ratio_subnational_panel` | `data/vintages/derived/minimum_wage_bite_ratio_subnational_panel@2026-05-14T111058Z.parquet` | Treat as present derived treatment panel; rerun only, no fetch needed. | `federal_minimum_wage_employment_meta` |
| `oecd:DSD_PDB@DF_PDB_PT` | `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet` | Alias legacy PDB PT token to landed `DSD_PDB`; use only after filtering measure/activity/unit to the intended productivity/RD concept. | `oecd_product_market_deregulation_tfp_panel` |
| `oecd:gdp_per_hour_worked_growth` | `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet` | Derive annual growth from PDB GDP-per-hour/labour-productivity rows. | `frontier_real_wage_growth_market_competition_1980_2024` |
| `oecd:avwage_growth_real` | `data/vintages/oecd/OECD.ELS.SAE_DSD_EARNINGS_DF_EARN_1.0@2026-05-04T192430Z.parquet` and `data/vintages/oecd/OECD.ELS.SAE_DSD_EARNINGS_DF_EARNINGS_1.0@2026-05-01T071721Z.parquet` | Derive real average-wage growth after selecting the appropriate earnings measure and deflator. | `frontier_real_wage_growth_market_competition_1980_2024` |
| `oecd:union_density` | `data/vintages/oecd/OECD.ELS.SAE_DSD_TUD_CBC_DF_TUD_1.0@2026-05-01T071140Z.parquet` and `data/vintages/oecd/TUD@2026-05-05T195705Z.parquet` | Alias to OECD TUD trade-union-density vintages. | `frontier_real_wage_growth_market_competition_1980_2024` |
| `oecd_pmr:barriers_to_entry` | `data/vintages/oecd_pmr/BARRIER_ENTRY@2026-05-02T220000Z.parquet` | Existing runner alias is safe; rerun can use local PMR barrier panel. | `frontier_real_wage_growth_market_competition_1980_2024` |
| `fraser_efw:regulation_business` | `data/vintages/fraser_efw/regulation@2026-05-02T220000Z.parquet` | Existing runner alias to Fraser regulation is safe as a broad business-regulation proxy; keep source tag distinct from PMR. | `frontier_real_wage_growth_market_competition_1980_2024` |
| `oecd:OECD.SDD.STES,DSD_KEI@DF_KEI,4.0` | `data/vintages/oecd/OECD.ECO.MAD_DSD_KEI_DF_KEI_1.0@2026-05-01T071721Z.parquet` | Alias exact STES/KEI token to landed KEI vintage only after selecting short-term interest-rate rows. | `private_credit_growth_crisis_predictor_oecd` |
| `oecd:OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.2` | `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet` and `data/vintages/oecd_pmr/OECD.ECO.GCRD_DSD_PMR_DF_PMR_1.2@2026-05-04T194708Z.parquet` | Alias PMR canonical token to landed PMR vintages; validate direction because lower PMR means more liberalization. | institutional market-index spine, `top_1_percent_income_share_growth_drivers` concentration proxy candidate |
| `oecd_pmr:pmr_services` | `data/vintages/oecd_pmr/PMR@2026-05-05T200616Z.parquet`, `data/vintages/oecd_pmr/NETWORK_SECTORS@2026-05-02T220000Z.parquet`, `data/vintages/oecd_pmr/REGULATIONS@2026-05-02T220000Z.parquet` | Derive services/network-sector PMR subset; do not treat as a concentration measure. | `sectoral_competition_services_productivity` |
| `oecd_stan:va_per_hour_services` | `data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet` | Derive services value-added per hour after country/industry/year validation. | `sectoral_competition_services_productivity` |
| `oecd:OECD.SDD.NAD,DSD_NAMAIN1@DF_TABLE3,1.0` | `data/vintages/eurostat/nama_10_a10@2026-05-12T133951Z.parquet` for Europe-rich subset; `data/vintages/oecd/OECD.SDD.NAD_DSD_NAMAIN1_DF_TABLE1_1.0@2026-05-01T071213Z.parquet` for national accounts totals | Hold for exact OECD Table 3. A Europe-only derived subset is locally possible, but not an exact full-OECD repair. | `financialisation_industry_share_decoupling` |
| `irena:solar_pv_costs`, `irena:wind_lcoe` | `data/vintages/irena/lcoe_solar_pv@2026-05-12T125721Z.parquet`, `data/vintages/irena/lcoe_wind_onshore@2026-05-12T125721Z.parquet` | Existing runner alias is safe; local continuation runs already use these files. | IRENA renewable learning continuation |

## Hold Notes

- Do not collapse Fraser, Heritage, PMR, and Doing Business into a single interchangeable treatment without source-family tags.
- PMR vintages currently provide limited within-country time variation for some panels; an alias repair can remove "vintage not on disk" without solving treatment-variation sufficiency.
- `top_1_percent_income_share_growth_drivers` has WID locally, but the exact missing `market_concentration_herfindahl` concept is not repaired by PMR alone.
- `financialisation_industry_share_decoupling` can be revived as a Eurostat subset, but the exact full-OECD Table 3 finance-industry source remains absent locally.
