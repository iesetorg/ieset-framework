# Financial Fragility Swarm C2 - 2026-05-18

Scope: Worker C lane for financial fragility, BIS credit/DSR/SPP, QE/Minsky, and financialisation/private-credit artifacts. I did not edit scoreboard/positions or the known dirty `data/manifests/fetch_run_2026-05-17T2317*` and daily-rate-limited backfill artifacts.

## Artifact Summary

| Hypothesis | Action | Verdict |
| --- | --- | --- |
| `private_credit_growth_crisis_predictor_oecd` | wrapper rerun + new exact provenance manifest | PARTIAL |
| `qe_financialisation_minsky_channel_2008_2021` | added wrapper + wrapper rerun + new exact provenance manifest | INCONCLUSIVE_DATA_PENDING |
| `gfc_balance_sheet_recession_post_2008_household_dual_mandate` | wrapper rerun + new exact provenance manifest | INCONCLUSIVE_DATA_PENDING |
| `financialisation_industry_share_decoupling` | wrapper rerun + new exact provenance manifest | INCONCLUSIVE_DATA_PENDING |
| `household_debt_minsky_cycle_2008` | wrapper rerun + new exact provenance manifest | REFUTED |
| `market_order_control_corruption_private_credit_depth_panel` | wrapper rerun + new exact provenance manifest | REFUTED |
| `market_order_sound_money_private_credit_depth_panel` | wrapper rerun + new exact provenance manifest | PARTIAL |
| `market_order_tax_burden_private_credit_depth_panel` | wrapper rerun + new exact provenance manifest | PARTIAL |
| `bis_credit_gap_private_investment_reversal_panel` | wrapper verified existing artifact/manifest; no file change kept | INCONCLUSIVE_DATA_PENDING |

## Verdict Notes

- `private_credit_growth_crisis_predictor_oecd`: remains PARTIAL; coefficient is `+0.1995`, p=`0.225`, above the preregistered significance gate.
- `qe_financialisation_minsky_channel_2008_2021`: current wrapper resolves more local controls than the stale card, but still has only 14 complete rows and is missing wage-growth, household financial-asset Gini, and nonfinancial corporate profit-share channels.
- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`: not repairable with current local data; household-saving-rate treatment has no within-country variation under the country-FE specification, and corporate net-lending plus ZLB controls remain missing.
- `financialisation_industry_share_decoupling`: current runner supersedes the stale partial card; the post-1980 constructed treatment is absorbed/no-within variation under fixed effects, while the exact finance-insurance VA series is not locally loaded.
- `household_debt_minsky_cycle_2008`: current wrapper produces a material opposite-signed result, `+0.3776`, p=`0.00198`; classified REFUTED against the registered negative direction.
- `market_order_control_corruption_private_credit_depth_panel`: REFUTED; coefficient `-13.37`, p=`0.0883`, opposite the positive claim direction.
- `market_order_sound_money_private_credit_depth_panel`: PARTIAL; coefficient `+0.116`, p=`0.505`.
- `market_order_tax_burden_private_credit_depth_panel`: PARTIAL; coefficient `+1.447`, p=`0.283`.
- `bis_credit_gap_private_investment_reversal_panel`: exact BIS artifact already had a manifest; wrapper reused the pre-existing artifact. The coefficient and raw contrast clear directionally, but only 14 countries are usable versus the preregistered 20-country coverage gate.

## Files Changed

- `engine/runs/private_credit_growth_crisis_predictor_oecd/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/qe_financialisation_minsky_channel_2008_2021/{diagnostics.json,result_card.md,replication.py,manifest.yaml}`
- `engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/financialisation_industry_share_decoupling/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/household_debt_minsky_cycle_2008/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/market_order_control_corruption_private_credit_depth_panel/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/market_order_sound_money_private_credit_depth_panel/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/runs/market_order_tax_burden_private_credit_depth_panel/{diagnostics.json,result_card.md,manifest.yaml}`
- `engine/audits/financial_fragility_swarm_C2_2026-05-18.md`

## Commands Run

```sh
python3 -m py_compile engine/runs/private_credit_growth_crisis_predictor_oecd/replication.py engine/runs/qe_financialisation_minsky_channel_2008_2021/replication.py engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/replication.py engine/runs/financialisation_industry_share_decoupling/replication.py engine/runs/household_debt_minsky_cycle_2008/replication.py engine/runs/market_order_control_corruption_private_credit_depth_panel/replication.py engine/runs/market_order_sound_money_private_credit_depth_panel/replication.py engine/runs/market_order_tax_burden_private_credit_depth_panel/replication.py engine/runs/bis_credit_gap_private_investment_reversal_panel/replication.py
python3 engine/runs/private_credit_growth_crisis_predictor_oecd/replication.py
python3 engine/runs/qe_financialisation_minsky_channel_2008_2021/replication.py
python3 engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/replication.py
python3 engine/runs/financialisation_industry_share_decoupling/replication.py
python3 engine/runs/household_debt_minsky_cycle_2008/replication.py
python3 engine/runs/market_order_control_corruption_private_credit_depth_panel/replication.py
python3 engine/runs/market_order_sound_money_private_credit_depth_panel/replication.py
python3 engine/runs/market_order_tax_burden_private_credit_depth_panel/replication.py
python3 engine/runs/bis_credit_gap_private_investment_reversal_panel/replication.py
python3 - <<'PY'  # generated eight manifest.yaml files from diagnostics and local vintage hashes
git restore -- engine/audits/bis_batch01_credit_cycle_results_2026-05-12.md
python3 - <<'PY'  # parsed all eight new manifests and checked hypothesis_id/status/vintages
python3 -m py_compile engine/runs/private_credit_growth_crisis_predictor_oecd/replication.py engine/runs/qe_financialisation_minsky_channel_2008_2021/replication.py engine/runs/gfc_balance_sheet_recession_post_2008_household_dual_mandate/replication.py engine/runs/financialisation_industry_share_decoupling/replication.py engine/runs/household_debt_minsky_cycle_2008/replication.py engine/runs/market_order_control_corruption_private_credit_depth_panel/replication.py engine/runs/market_order_sound_money_private_credit_depth_panel/replication.py engine/runs/market_order_tax_burden_private_credit_depth_panel/replication.py engine/runs/bis_credit_gap_private_investment_reversal_panel/replication.py
git diff --check
git status --short
```

Arrow emitted sandbox CPU-info `sysctlbyname` warnings during parquet reads; all wrapper commands still exited 0.

## Blockers

- QE/Minsky needs exact wage-growth, LIS/OECD household financial-asset inequality, and nonfinancial corporate profit-share vintages before its three-gate preregistration can be adjudicated.
- GFC balance-sheet recession needs the nonfinancial-corporate net-lending panel and ZLB short-rate indicator; the local household-saving-rate bridge is not usable with the registered country-FE treatment.
- Financialisation industry-share needs the exact finance-insurance value-added series or a redesigned non-absorbed treatment; the current post-1980 dummy has no within-country identifying variation in the registered FE model.
- BIS private-investment reversal needs broader country coverage to clear its own gate; effect direction is negative but coverage remains 14 countries.

## Restored Churn

- Restored incidental wrapper churn in `engine/audits/bis_batch01_credit_cycle_results_2026-05-12.md`.
- Left unrelated/out-of-lane worktree churn untouched, including `web/app/scoreboard/page.tsx`, `data/manifests/fetch_run_2026-05-17T2317*`, the daily-rate-limited backfill files, and newly observed non-C2 changes under green/trade/consumer run directories such as `engine/runs/green_transition_cost_trajectory_electricity_prices/`, `engine/runs/consumer_choice_variety_trade_market_reform/`, and `engine/runs/export_complexity_market_access_vs_subsidy/`.
