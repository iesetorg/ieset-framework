# Data-Gap Unlock Assessment

- generated_utc: `2026-05-12`
- purpose: summarize the deep data-dive round and identify which hypothesis tracks can now move from data repair to replication/rerun.

## Fresh Data Landed

| cluster | source | rows | period | status |
| --- | --- | ---: | --- | --- |
| intergenerational mobility | `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0` | 5,286 | 2016-2022 | landed |
| intergenerational mobility / housing channel | `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0` | 110,277 | 2004-2026 | landed |
| migration / labour | `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0` | 2,711 | 2000-2024 | landed |
| migration / labour | `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_NUP_SEX,1.0` | 14,218 | 2000-2024 | landed |
| migration / labour | `oecd:OECD.ELS.IMD,DSD_MIG_F@DF_MIG_POPF,1.0` | 197,570 | 1995-2024 | landed |
| minimum wage | `bls:OEWS_state_p10_hourly_wage_panel` | 474 | 2014-2024 | landed after archive parser repair |
| minimum wage | `bls:OEWS_state_median_hourly_wage_panel` | 474 | 2014-2024 | landed after archive parser repair |
| minimum wage | `derived:minimum_wage_bite_ratio_state_panel` | 474 | 2014-2024 | built from USDOL state minimum wage / BLS median wage |
| minimum wage | `derived:minimum_wage_low_tail_bite_ratio_state_panel` | 474 | 2014-2024 | built from USDOL state minimum wage / BLS p10 wage |
| renewables LCOE | `irena:lcoe_solar_pv` | 15 | 2010-2024 | landed from official 2024 data workbook |
| renewables LCOE | `irena:lcoe_wind_onshore` | 15 | 2010-2024 | landed from official 2024 data workbook |

Total fresh usable rows: 331,988.

## Fetcher / Parser Repairs

- Added `scripts/fetch_gap_roundup_zenrows_2026_05_12.py` for cluster-based gap roundups with optional ZenRows stdin key handling.
- Added `scripts/discover_gap_source_urls_2026_05_12.py` to discover official publisher download URLs and write audit artifacts without storing API keys.
- Extended `data/fetchers/bls.py` with official BLS OEWS state archive parsing for 2014-2024 state p10 and median hourly wage panels.
- Fixed the OEWS state series id construction for current time-series smoke checks.
- Extended `data/fetchers/irena.py` so `lcoe_solar_pv` and `lcoe_wind_onshore` parse the official IRENA 2024 workbook's `Fig S.1` LCOE rows rather than the contents sheet.
- Added `scripts/build_minimum_wage_bite_panels_2026_05_12.py` to materialize state-level minimum-wage bite ratios from already-fetched USDOL and BLS inputs.

## Newly Unblocked Hypothesis Tracks

1. Minimum-wage bite-ratio tests
   - `minimum_wage_disemployment_at_high_bite_ratios`
   - `minimum_wage_employment_effect_us_states`
   - `minimum_wage_above_median_employment_teen_effects`
   - What changed: the wage-denominator side of the bite ratio is now available as a state-year panel for 2014-2024, and the derived median/p10 bite-ratio panels have been materialized. The remaining blocker is teen or low-skill employment outcomes, not wage percentiles.

2. China renewables / learning-curve tests
   - `china_renewables_global_learning_curve_spillover`
   - `solar_lcoe_2010_2024_learning_curve_continuation`
   - What changed: official IRENA solar PV and onshore-wind LCOE series now exist locally for 2010-2024. Capacity vintages were already present from the earlier IRENA PxWeb round.

3. Migration labour-market tests
   - `demo_migration_inflows_wages_skill_split`
   - `migration_labor_market_complement_not_substitute`
   - `migration_labor_market_openness_qol`
   - `net_migration_revealed_preference_market_institutions`
   - What changed: OECD migration stocks, employment by education, and labour-force rates by sex are now present. Some specs still name the older DIOC flow directly, so reruns may need a controlled source substitution rather than a blind run.

4. Intergenerational mobility channel tests
   - `intergenerational_mobility_cross_country`
   - `intergenerational_mobility_institutional_determinants`
   - What changed: OECD education finance and housing inequality channels are present. The primary mobility outcome still needs explicit confirmation against the current local OWID/OECD mirror.

## Still Real Blockers

- Occupational licensing: `kleiner_krueger` still needs a valid manual or official static data file. The fetcher knows the schema, but no source file is locally present.
- Wealth tax: `data/manual/wealth_tax/revenue_forecast_realized.csv` is still missing. This is not a scraping failure; it needs sourced country-tax-year rows.
- Minimum wage: the state wage panel is now fixed, but the full high-bite design still needs teen employment-to-population or low-skill employment outcomes aligned to the same states and years.
- Migration skill split: the newly landed OECD migration flows are strong substitutes for some tests, but DIOC-specific hypotheses should be upgraded deliberately so the measured concept remains honest.

## Next Processing Strategy

1. Rerun the two cleanest renewables tests first because the IRENA outcome gap is now directly closed.
2. Rerun or upgrade the minimum-wage tests after adding teen/low-skill employment outcomes.
3. For migration, patch specs only where the OECD IMD flows measure the same construct as the old DIOC placeholder; otherwise create new, cleaner hypotheses from the landed IMD data.
4. Keep occupational licensing and wealth tax in manual-source repair until publisher tables are actually present.

## Audit Trail

- `engine/audits/data_gap_roundup_zenrows_2026-05-12T120410Z.md`
- `engine/audits/data_gap_roundup_zenrows_2026-05-12T120817Z.md`
- `engine/audits/data_gap_source_discovery_2026-05-12T122042Z.md`
- `engine/audits/data_gap_roundup_zenrows_2026-05-12T125721Z.md`
- `engine/audits/minimum_wage_bite_panel_build_2026-05-12T130133Z.json`
