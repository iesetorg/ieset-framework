# Macro Financial Swarm A - 2026-05-18

Scope: Worker A macro/monetary/financial lane only. I did not edit scoreboard/positions or the known dirty `data/manifests/fetch_run_2026-05-17T2317*` and daily-rate-limited backfill artifacts.

## Candidate Selection

Targeted 12 local-data candidates:

| Hypothesis | Action | Verdict |
| --- | --- | --- |
| `austrian_monetary_expansion_asset_bubble_not_cpi_panel` | bespoke exact local-proxy wrapper + manifest/result card | REFUTED |
| `financial_negative_rates_eurozone_2014_2022` | bespoke exact local-proxy wrapper + manifest/result card | PARTIAL |
| `mena_egypt_floatation_episodes_2016_2024` | annual WDI repair wrapper + manifest/result card | PARTIAL |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | manifest repair for existing real verdict | SUPPORTED |
| `financial_fed_dot_plot_realised_path_2012_2024` | manifest repair for existing real verdict | SUPPORTED |
| `financial_boe_independence_1997_macroprudential_2013` | manifest repair for existing real verdict | SUPPORTED |
| `abenomics_monetary_fiscal_coordination_effect` | manifest repair for existing real verdict | SUPPORTED |
| `abenomics_monetary_policy_demand_effect` | manifest repair for existing real verdict | REFUTED |
| `fiat_expansion_erodes_currency_purchasing_power_long_run` | manifest repair for existing real verdict | SUPPORTED |
| `market_order_sound_money_gdp_pc_growth_panel` | manifest repair for existing real verdict | SUPPORTED |
| `monetary_finance_zlb_no_inflation` | manifest repair for existing real verdict | REFUTED |
| `euro_area_fiscal_constraint_contractionary_effect` | manifest repair for existing real verdict | REFUTED |

## New Repairs

### `austrian_monetary_expansion_asset_bubble_not_cpi_panel`

Verdict: **REFUTED**.

Exact local proxy: BIS real residential property prices, WDI broad money/GDP annual change, WDI CPI inflation, WDI real GDP growth, and WDI trade openness over 1987-2007. Usable panel: 147 observations across 7 countries. Money-growth proxy coefficient in the asset-price regression is `+0.0445` with p=`0.305`; it fails the required positive/significant asset coefficient gate.

### `financial_negative_rates_eurozone_2014_2022`

Verdict: **PARTIAL**.

ECB DFR/Euribor/M3 proxy gates show short-end passthrough and no broad-money run: average Euribor 3M minus DFR spread is `9.37bp`, Euribor is below zero in `86/98` months, and M3 annual growth never turns negative. The exact rule is not fully satisfied because M3 growth is `+3.92pp` above the 2010-2013 mean, and the registered Eonia/ESTR, household-deposit, and core-sovereign-yield gates are not locally loaded.

### `mena_egypt_floatation_episodes_2016_2024`

Verdict: **PARTIAL**.

Annual WDI repair confirms the repeated official devaluation pattern, but not a homogeneous full event-study pattern. 2016 clears FX/reserve/inflation gates; 2022 clears FX/inflation but not reserves; 2024 clears FX/reserves with 2025 pending but not a new CPI acceleration relative to already-high 2023 inflation. The parallel-vs-official gap is not locally loaded.

## Existing Real Verdicts Manifested

Added exact provenance manifests, without rerunning timestamps, for:

- `financial_fed_reverse_repo_facility_usage_2021_2024`: SUPPORTED; ON RRP peak/decline gates clear.
- `financial_fed_dot_plot_realised_path_2012_2024`: SUPPORTED; generic descriptive pre/post gap remains real, with missing SEP dot caveat preserved in diagnostics.
- `financial_boe_independence_1997_macroprudential_2013`: SUPPORTED; inflation-volatility pre/post gate clears.
- `abenomics_monetary_fiscal_coordination_effect`: SUPPORTED; ITS post-2013 gap positive.
- `abenomics_monetary_policy_demand_effect`: REFUTED; ITS sign is opposite the registered claim.
- `fiat_expansion_erodes_currency_purchasing_power_long_run`: SUPPORTED; 7/7 sampled fiat currencies lose purchasing power against at least one hard-asset benchmark.
- `market_order_sound_money_gdp_pc_growth_panel`: SUPPORTED; inflation-rate coefficient is `-0.06927`, p=`0.00238`.
- `monetary_finance_zlb_no_inflation`: REFUTED; USA CPI breaches the registered 3% window thresholds.
- `euro_area_fiscal_constraint_contractionary_effect`: REFUTED; coefficient is opposite the registered contractionary-effect sign.

## Commands Run

```sh
python3 scripts/run_event_study.py mena_egypt_floatation_episodes_2016_2024
python3 scripts/run_panel_fe.py austrian_monetary_expansion_asset_bubble_not_cpi_panel
python3 scripts/run_panel_fe.py interest_rate_hike_distributional_upward_redistribution
python3 scripts/run_panel_fe.py post_covid_inflation_episode_supply_vs_demand_decomposition
python3 scripts/run_panel_fe.py gfc_balance_sheet_recession_post_2008_household_dual_mandate
python3 scripts/run_multi_metric_checklist.py currency_user_vs_issuer_hyperinflation_classification
python3 scripts/run_multi_metric_checklist.py zimbabwe_property_rights_output_link
python3 -m py_compile engine/runs/austrian_monetary_expansion_asset_bubble_not_cpi_panel/replication.py engine/runs/financial_negative_rates_eurozone_2014_2022/replication.py engine/runs/mena_egypt_floatation_episodes_2016_2024/replication.py
python3 engine/runs/austrian_monetary_expansion_asset_bubble_not_cpi_panel/replication.py
python3 engine/runs/financial_negative_rates_eurozone_2014_2022/replication.py
python3 engine/runs/mena_egypt_floatation_episodes_2016_2024/replication.py
python3 - <<'PY'  # generated manifest.yaml files from diagnostics/local vintage hashes for the 9 existing real verdicts
git restore -- engine/runs/currency_user_vs_issuer_hyperinflation_classification/diagnostics.json engine/runs/currency_user_vs_issuer_hyperinflation_classification/manifest.yaml engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/diagnostics.json engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/result_card.md engine/runs/interest_rate_hike_distributional_upward_redistribution/diagnostics.json engine/runs/interest_rate_hike_distributional_upward_redistribution/result_card.md engine/runs/post_covid_inflation_episode_supply_vs_demand_decomposition/diagnostics.json engine/runs/post_covid_inflation_episode_supply_vs_demand_decomposition/result_card.md engine/runs/zimbabwe_property_rights_output_link/diagnostics.json engine/runs/zimbabwe_property_rights_output_link/manifest.yaml
python3 -m py_compile engine/runs/austrian_monetary_expansion_asset_bubble_not_cpi_panel/replication.py engine/runs/financial_negative_rates_eurozone_2014_2022/replication.py engine/runs/mena_egypt_floatation_episodes_2016_2024/replication.py engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024/replication.py engine/runs/financial_fed_dot_plot_realised_path_2012_2024/replication.py engine/runs/financial_boe_independence_1997_macroprudential_2013/replication.py engine/runs/abenomics_monetary_fiscal_coordination_effect/replication.py engine/runs/abenomics_monetary_policy_demand_effect/replication.py engine/runs/fiat_expansion_erodes_currency_purchasing_power_long_run/replication.py engine/runs/market_order_sound_money_gdp_pc_growth_panel/replication.py engine/runs/monetary_finance_zlb_no_inflation/replication.py engine/runs/euro_area_fiscal_constraint_contractionary_effect/replication.py
python3 -c "..."  # parsed the 12 manifest.yaml files and checked hypothesis_id/verdict labels
python3 -c "..."  # checked the three new bespoke diagnostics runner/run_utc/verdict labels
git status --short
```

## Blockers

- `interest_rate_hike_distributional_upward_redistribution`: primary OECD/LIS distributional national-accounts quintile data are not locally loaded; generic runner listwise-deletes to zero rows.
- `post_covid_inflation_episode_supply_vs_demand_decomposition`: registered Bernanke-Blanchard structural decomposition needs GSCPI/shadow-rate/fiscal-impulse/wage inputs not present in the local panel; generic runner has zero complete rows.
- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`: generic panel run finds no within-country variation under country fixed effects for the loaded household-saving-rate treatment.
- `currency_user_vs_issuer_hyperinflation_classification`: no machine-readable episode-level checklist metrics loaded; multi-metric runner reports `0M/0N/0PD/0PE`.
- `zimbabwe_property_rights_output_link`: remains a draft/stub checklist; generic checklist has no canonical metrics to evaluate.

## Restored Churn

Restored generic-rerun churn for the blocked/inconclusive attempts listed above. Kept only the three bespoke repairs, the nine provenance manifests, and this audit.
