# Trade / Product Worker C Audit - 2026-05-18

Worker: C

Scope: trade/product/market-access graduation candidates and adjacent product-concentration/diversification specs. I did not edit scoreboard or position files. I did not edit hypothesis YAMLs because the newly available data did not justify changing any preregistered estimand.

## Data Gate

Local WITS product concentration is real and loadable:

- `wits:export_product_hhi_wits`
- Vintage: `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet`
- Rows: 4,669 exporter-years
- Countries: 207 reporter ISO3s
- Years: 1988-2022
- Schema includes `country_iso3`, `year`, `value`, `number_of_products`, `classification`, `partner_iso3`, `product_cluster`
- Meaning: exporter-to-world product-export HHI; higher `value` means more concentrated exports.

Local broad WDI-derived diversification proxies are also loadable:

- `derived:export_diversification_index`
- `derived:export_concentration_hhi_broad`
- Vintage stamp: `2026-05-16T085311Z`
- Rows: 9,623 country-years, 241 ISO3s, 1962-2024

Important limit: WITS HHI is an export concentration benchmark. It is not an import variety count, tariff series, bilateral trade-flow series, raw HS6 product-line panel, RCA/Theil-from-product-shares source, or TiVA/GVC source.

## Rerun Verdicts

| Hypothesis | Command | Verdict | Useful data change | Graduation judgment |
| --- | --- | --- | --- | --- |
| `export_complexity_market_access_vs_subsidy` | `python3 scripts/run_panel_fe.py export_complexity_market_access_vs_subsidy --force` | `INCONCLUSIVE_DATA_PENDING` | `un_comtrade:export_product_concentration` now resolves to WITS HHI (`n=4669`). | Still blocked. The registered decomposition still requires `world_bank_wits:high_tech_exports` and `un_comtrade:unique_hs6_products`; the primary ECI outcome, market-access/subsidy treatments, initial ECI, and exchange-rate-volatility control remain absent. |
| `consumer_choice_variety_trade_market_reform` | `python3 scripts/run_panel_fe.py consumer_choice_variety_trade_market_reform --force` | `INCONCLUSIVE_DATA_PENDING` | `pwt:rconna` now loads as the welfare outcome (`n=10399`). | Still blocked. The true product-variety outcome (`un_comtrade:product_lines; world_bank_wits:product_concentration`) is not on disk, constructed trade-liberalisation and industrial-policy treatments are absent, and the PMR competition treatment has no within-country variation under country FE. |
| `quality_adjusted_consumption_market_liberal_panel` | `python3 scripts/run_panel_fe.py quality_adjusted_consumption_market_liberal_panel --force` | `PARTIAL` | PWT real consumption outcome loads cleanly. | Graduated only as a real consumption panel, not as a product-variety/quality-adjusted claim. Estimate: `coef=-0.03337`, `p=0.189`, `n=954`, `countries=37`; direction remains inconclusive and the product-variety outcome is still missing. |
| `export_openness_agricultural_diversification` | `python3 scripts/run_panel_fe.py export_openness_agricultural_diversification --force` | `PARTIAL` | Existing WDI agriculture-export-share proxy remains fully runnable. | Real but weak proxy result. Estimate: `coef=-2.498`, `p=0.691`, `n=1155`, `countries=23`; not supported or refuted. No WITS product data were needed by the registered spec. |
| `global_value_chain_participation_upgrade` | `python3 scripts/run_panel_fe.py global_value_chain_participation_upgrade --force` | `INCONCLUSIVE_DATA_PENDING` | No relevant WITS unlock. | Still blocked: TiVA/GVC participation, backward linkages, forward linkages, and real manufacturing earnings are absent; current complete-case fallback remains `n=23`. |
| `tariff_protection_duration_growth_drag` | `python3 scripts/run_panel_fe.py tariff_protection_duration_growth_drag --force` | `INCONCLUSIVE_DATA_PENDING` | No relevant WITS HHI unlock. | Still blocked: applied weighted-mean tariff and constructed protection-duration treatment are absent. WITS HHI does not substitute for tariff exposure or import value. |
| `trade_openness_long_run_income_convergence` | `python3 scripts/run_panel_fe.py trade_openness_long_run_income_convergence --force` | `PARTIAL` | Existing PWT/WDI panel remains runnable. | Real but not a product-channel graduation. Estimate is effectively zero despite small p-value: `coef=+6.729e-18`, `p=0.00881`, `n=1281`, `countries=61`. Industrial-policy treatment and product/import decomposition channels remain absent. |

## Resource Developmentalism Note

The 2026-05-17 resource-developmentalism audit said the local WITS workbook was only a URL catalog. That measurement gate is now partly superseded: the WITS HHI payloads have since been materialized into `wits:export_product_hhi_wits`.

That does not make `resource_developmentalism_rent_seeking_trap` scoreboard-safe. The subtype audit's core identification blocker still holds: clean treated/comparator subtype coding has no within-country treatment variation under country FE, and the generic `movements:resource_developmentalism` treatment remains too noisy for a high-quality causal score. A hardened resource run should use the subtype sidecar plus an estimator compatible with mostly between-country assignment before replacing the broad WDI-derived export-diversification proxy with WITS HHI.

## Blockers

- Import/product-line variety is still absent. This blocks consumer-choice variety and any claim needing `un_comtrade:product_lines` or true domestic SKU/import HS6 counts.
- WITS tariff and trade-flow data are still absent. This blocks tariff-duration and market-access claims needing `world_bank_wits:weighted_mean_applied_tariff`, `world_bank_wits:import_value`, or bilateral/product trade values.
- Raw product-line microdata are still absent. WITS HHI can benchmark concentration, but it cannot produce preregistered HS6 counts, Theil indices from product shares, top-product shares, RCA, or sector baskets without new derived vintages.
- OECD TiVA/GVC data are still absent. WITS product HHI does not address `oecd_tiva:gvc_participation`, backward linkages, or forward linkages.
- Atlas ECI is still absent. WITS HHI can serve as a secondary concentration outcome, but it is not the Hausmann-Hidalgo ECI primary outcome.
- Several specs still cite constructed treatments without local vintages: Wacziarg-Welch trade-liberalisation dates, market-access/competition composites, subsidy/industrial-policy composites, state ownership/sector targeting, and tariff-duration spells.

## Commands Run

```sh
git status --short
sed -n '1,240p' engine/audits/runnable_graduation_queue_2026-05-16.md
sed -n '1,260p' engine/audits/graduation_data_pack_macro_trade_labour_2026-05-16.md
sed -n '1,260p' engine/audits/resource_developmentalism_subtype_testability_audit_2026-05-17.md
sed -n '1,260p' scripts/build_export_diversification_vintage.py
sed -n '1,260p' data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json
rg --files | rg '(^hypotheses/|engine/runs/).*(export_complexity_market_access_vs_subsidy|consumer_choice_variety_trade_market_reform|quality_adjusted_consumption_market_liberal_panel|export_openness_agricultural_diversification|global_value_chain_participation_upgrade|product|diversification)'
rg -n 'export_complexity_market_access_vs_subsidy|consumer_choice_variety_trade_market_reform|quality_adjusted_consumption_market_liberal_panel|export_openness_agricultural_diversification|global_value_chain_participation_upgrade|product concentration|export_product_hhi_wits|world_bank_wits:product_concentration|un_comtrade:export_product_concentration|product_concentration' .
find data/vintages -maxdepth 2 -type f | sort | rg 'wits|derived|world_bank_wdi|unctad|comtrade'
python3 scripts/run_panel_fe.py export_complexity_market_access_vs_subsidy --force
python3 scripts/run_panel_fe.py consumer_choice_variety_trade_market_reform --force
python3 scripts/run_panel_fe.py quality_adjusted_consumption_market_liberal_panel --force
python3 scripts/run_panel_fe.py export_openness_agricultural_diversification --force
python3 scripts/run_panel_fe.py global_value_chain_participation_upgrade --force
rg -n 'export_product_concentration|product_concentration|export_product_hhi|export_diversification_index|export_concentration_hhi_broad|unique_hs6_products|product_lines|product diversification|product concentration' hypotheses engine/runnability.derived.yaml engine/runs -g '*.yaml' -g '*.md' -g '*.json'
python3 -c "import pandas as pd; from pathlib import Path; paths=['data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet','data/vintages/derived/export_diversification_index@2026-05-16T085311Z.parquet','data/vintages/derived/export_concentration_hhi_broad@2026-05-16T085311Z.parquet']; ..."
python3 scripts/run_panel_fe.py tariff_protection_duration_growth_drag --force
python3 scripts/run_panel_fe.py trade_openness_long_run_income_convergence --force
git diff -- engine/runs/export_complexity_market_access_vs_subsidy/result_card.md engine/runs/export_complexity_market_access_vs_subsidy/diagnostics.json engine/runs/consumer_choice_variety_trade_market_reform/result_card.md engine/runs/consumer_choice_variety_trade_market_reform/diagnostics.json engine/runs/quality_adjusted_consumption_market_liberal_panel/result_card.md engine/runs/quality_adjusted_consumption_market_liberal_panel/diagnostics.json engine/runs/export_openness_agricultural_diversification/result_card.md engine/runs/export_openness_agricultural_diversification/diagnostics.json engine/runs/global_value_chain_participation_upgrade/result_card.md engine/runs/global_value_chain_participation_upgrade/diagnostics.json engine/runs/tariff_protection_duration_growth_drag/result_card.md engine/runs/tariff_protection_duration_growth_drag/diagnostics.json engine/runs/trade_openness_long_run_income_convergence/result_card.md engine/runs/trade_openness_long_run_income_convergence/diagnostics.json
python3 -c "import json; files=['engine/runs/export_complexity_market_access_vs_subsidy/diagnostics.json','engine/runs/consumer_choice_variety_trade_market_reform/diagnostics.json','engine/runs/quality_adjusted_consumption_market_liberal_panel/diagnostics.json','engine/runs/export_openness_agricultural_diversification/diagnostics.json','engine/runs/global_value_chain_participation_upgrade/diagnostics.json','engine/runs/tariff_protection_duration_growth_drag/diagnostics.json','engine/runs/trade_openness_long_run_income_convergence/diagnostics.json']; [json.load(open(f)) for f in files]; print('validated', len(files), 'diagnostics json files')"
```

The Python/parquet reads emitted benign Arrow `sysctlbyname` sandbox warnings; the commands completed successfully.

## Write Scope

Touched run artifacts:

- `engine/runs/export_complexity_market_access_vs_subsidy/result_card.md`
- `engine/runs/export_complexity_market_access_vs_subsidy/diagnostics.json`
- `engine/runs/consumer_choice_variety_trade_market_reform/result_card.md`
- `engine/runs/consumer_choice_variety_trade_market_reform/diagnostics.json`
- `engine/runs/quality_adjusted_consumption_market_liberal_panel/result_card.md`
- `engine/runs/quality_adjusted_consumption_market_liberal_panel/diagnostics.json`
- `engine/runs/export_openness_agricultural_diversification/result_card.md`
- `engine/runs/export_openness_agricultural_diversification/diagnostics.json`
- `engine/runs/global_value_chain_participation_upgrade/result_card.md`
- `engine/runs/global_value_chain_participation_upgrade/diagnostics.json`
- `engine/runs/tariff_protection_duration_growth_drag/result_card.md`
- `engine/runs/tariff_protection_duration_growth_drag/diagnostics.json`
- `engine/runs/trade_openness_long_run_income_convergence/result_card.md`
- `engine/runs/trade_openness_long_run_income_convergence/diagnostics.json`

New audit:

- `engine/audits/trade_product_worker_c_2026-05-18.md`

Concurrent/unrelated dirty files were present after the reruns in several non-trade run directories. I left them untouched.
