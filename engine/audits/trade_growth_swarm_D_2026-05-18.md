# Trade/Growth Swarm D Audit

Worker: D
Date: 2026-05-18
Scope: trade/product/industrial/growth hypotheses and corresponding run artifacts only. Scoreboard/positions not edited.

## Graduated Or Hardened

| Hypothesis | Lane | Action | Verdict |
| --- | --- | --- | --- |
| `trade_lib_india_1991_tariff_cut_export_response` | trade | Added exact manifest pinning WDI trade/export vintages for existing exact descriptive wrapper/result card. | SUPPORTED - trade openness rose +14.7pp, clearing the +10pp gate. |
| `trade_lib_indonesia_1980s_1990s_unilateral` | trade | Added exact manifest pinning WDI trade/manufacturing vintages for existing exact descriptive wrapper/result card. | REFUTED - trade openness rose only +1.9pp, below the +5pp refutation gate. |
| `trade_lib_egypt_fta_cascade` | trade | Added exact manifest pinning WDI trade/export vintages for existing exact descriptive wrapper/result card. | SUPPORTED - openness rose +16.1pp by 2007-2010, then post-2011 mean sat -21.3pp below peak. |
| `trade_lib_south_africa_sadc_trade` | trade | Added exact manifest pinning WDI trade/export vintages for existing exact descriptive wrapper/result card. | SUPPORTED - ZAF openness changed +13.3pp, inside the registered [-5,+20]pp band. |
| `trade_lib_chile_bilateral_fta_cascade` | trade | Added exact manifest pinning WDI trade/tariff vintages for existing exact descriptive wrapper/result card. | REFUTED - CHL openness rose +7.3pp but comparator differential moved -9.0pp. |
| `trade_lib_mexico_eu_fta_2000` | trade | Added exact manifest pinning WDI trade/export vintages for existing exact descriptive wrapper/result card. | REFUTED - MEX openness change lagged comparators by 6.1pp. |
| `trade_lib_colombia_us_fta_2012` | trade | Added exact manifest pinning WDI trade/export vintages for existing exact descriptive wrapper/result card. | SUPPORTED - COL openness change was within +1.4pp of comparator change. |
| `trade_lib_argentina_mercosur_industrial_effect` | trade | Added exact manifest pinning WDI manufacturing-share/value-added vintages for existing exact descriptive wrapper/result card. | SUPPORTED - ARG manufacturing-share change differed from comparators by only +1.6pp. |
| `asia_bangladesh_apparel_growth_1985_2024` | growth/trade | Added exact manifest pinning WDI growth, manufacturing, exports, population, and investment vintages for existing exact descriptive wrapper/result card. | SUPPORTED - manufacturing share +6.75pp and BGD-PAK growth gap +2.78pp/yr clear both primary gates. |
| `trade_lib_bangladesh_apparel_eu_eba_2008` | trade | Repaired run-local wrapper from generic descriptive fallback to exact preregistered Bangladesh-vs-Pakistan manufacturing-share gate; regenerated diagnostics, manifest, and result card. | SUPPORTED - BGD manufacturing share rose +5.62pp and beat PAK by +3.42pp. |

## Repair Notes

- `trade_lib_bangladesh_apparel_eu_eba_2008` previously had a REFUTED generic `panel_summary` result that compared Bangladesh's late-window export share to a donor median. That did not match the hypothesis falsification rule, which asks whether Bangladesh manufacturing-share-of-GDP rose by at least +4pp from 2000-2004 to 2015-2019 and beat Pakistan by at least +2pp. The run-local exact wrapper now implements that rule directly and records export-share context separately.
- The other nine selected runs already had real verdict cards and wrappers; the missing hardening layer was exact `manifest.yaml` vintage pinning.

## Deferred Candidates

- `tariff_protection_duration_growth_drag`: blocked by missing loadable tariff treatment (`world_bank_wits:weighted_mean_applied_tariff` / constructed cumulative tariff years).
- `export_complexity_market_access_vs_subsidy`: blocked by missing high-tech/product-count decomposition sources (`world_bank_wits:high_tech_exports`, `un_comtrade:unique_hs6_products`).
- `industrial_policy_semiconductor_chips_act_effectiveness`, `green_industrial_policy_global_chip_race_2022_2026`, `lula3_industrial_policy_2023_2026_reshoring_outcomes`: not mature enough for exact verdicts with local data; post-treatment windows and sector-specific series are missing or intentionally future-dated.
- `industrial_policy_without_exit_discipline_failure` and `national_champions_long_run_productivity_drag`: blocked by missing constructed treatment variables or firm concentration data.
- Several proxy-first panels (`export_processing_zone_wage_spillover`, `subsidised_industrial_zone_export_performance`, `import_competition_domestic_productivity_discipline`, `wto_accession_productivity_spillover`) produce near-zero mechanical coefficients under current constructed indicators; left as repair candidates rather than promoted.

## Verification

- `python3 -m py_compile engine/runs/trade_lib_bangladesh_apparel_eu_eba_2008/replication.py`
- `python3 -m py_compile` on the nine selected existing wrappers:
  `trade_lib_india_1991_tariff_cut_export_response`,
  `trade_lib_indonesia_1980s_1990s_unilateral`,
  `trade_lib_egypt_fta_cascade`,
  `trade_lib_south_africa_sadc_trade`,
  `trade_lib_chile_bilateral_fta_cascade`,
  `trade_lib_mexico_eu_fta_2000`,
  `trade_lib_colombia_us_fta_2012`,
  `trade_lib_argentina_mercosur_industrial_effect`,
  `asia_bangladesh_apparel_growth_1985_2024`.
- `python3 engine/runs/trade_lib_bangladesh_apparel_eu_eba_2008/replication.py`
- YAML parse check over all ten selected manifests.

## Churn / Restore Notes

- No scoreboard or position files were edited.
- Known/concurrent dirty files outside this lane were observed and left untouched, including `web/app/scoreboard/page.tsx`, `data/manifests/fetch_run_2026-05-17T2317*.yaml`, and `engine/audits/daily_rate_limited_data_backfill_2026-05-17T2317*`.
- Additional unrelated dirty fiscal/monetary run files and fiscal-tax swarm manifests were present during final status; they appear to be other-worker work and are not part of Worker D output.
- No Worker D file should be restored as timestamp-only churn. The only regenerated timestamped files are the Bangladesh EBA diagnostics/result/manifest produced by the new exact wrapper.
