# BIS Batch 01 Credit-Cycle Results - 2026-05-12

Runner: `scripts/promote_bis_batch01_credit_cycle_2026_05_12.py`.

## Verdict Tally

| Verdict | Count |
|---|---:|
| `INCONCLUSIVE_DATA_PENDING` | 2 |
| `PARTIAL` | 6 |
| `REFUTED` | 1 |
| `SUPPORTED` | 1 |

## Results

| Hypothesis | Verdict | Observations | Countries | Reason |
|---|---|---:|---:|---|
| `bis_credit_gap_house_price_reversal_oecd_1970_2025` | `PARTIAL` | 8038 | 41 | one of the regression or raw-contrast gates clears, but not both |
| `bis_credit_gap_unemployment_lag_panel_1970_2025` | `PARTIAL` | 9573 | 42 | pre-existing artifact reused; one of the regression or raw-contrast gates clears, but not both |
| `bis_credit_gap_dsr_joint_fragility_panel_1999_2025` | `PARTIAL` | 3366 | 17 | one of the regression or raw-contrast gates clears, but not both |
| `bis_household_dsr_consumption_slowdown_panel_1999_2025` | `REFUTED` | 3094 | 17 | pre-existing artifact reused; neither the regression nor raw-contrast gate clears |
| `bis_corporate_dsr_investment_slowdown_panel_1999_2025` | `INCONCLUSIVE_DATA_PENDING` | 364 | 2 | insufficient coverage for the predeclared gate |
| `bis_credit_gap_current_account_twin_deficit_risk` | `SUPPORTED` | 9086 | 42 | regression and raw contrast both clear the predeclared gates |
| `bis_credit_gap_low_real_rate_amplifier_panel` | `PARTIAL` | 5282 | 28 | one of the regression or raw-contrast gates clears, but not both |
| `bis_house_price_credit_gap_boom_bust_panel` | `PARTIAL` | 8038 | 41 | one of the regression or raw-contrast gates clears, but not both |
| `bis_credit_gap_private_investment_reversal_panel` | `INCONCLUSIVE_DATA_PENDING` | 3147 | 14 | insufficient coverage for the predeclared gate |
| `bis_long_horizon_credit_cycle_market_discipline_panel` | `PARTIAL` | 11433 | 42 | one of the regression or raw-contrast gates clears, but not both |

## Pre-existing Artifacts Reused

- `bis_credit_gap_unemployment_lag_panel_1970_2025`
- `bis_household_dsr_consumption_slowdown_panel_1999_2025`

## Blockers

- None for data-ready execution. Two IDs were skipped because complete diagnostics already existed in the working tree.

## Files Written

- `engine/audits/bis_batch01_credit_cycle_results_2026-05-12.md`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/chart_data.json`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/coefficients.parquet`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/diagnostics.json`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/manifest.yaml`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/replication.py`
- `engine/runs/bis_corporate_dsr_investment_slowdown_panel_1999_2025/result_card.md`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/chart_data.json`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/coefficients.parquet`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/diagnostics.json`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/manifest.yaml`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/replication.py`
- `engine/runs/bis_credit_gap_current_account_twin_deficit_risk/result_card.md`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/chart_data.json`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/coefficients.parquet`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/diagnostics.json`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/manifest.yaml`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/replication.py`
- `engine/runs/bis_credit_gap_dsr_joint_fragility_panel_1999_2025/result_card.md`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/chart_data.json`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/coefficients.parquet`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/diagnostics.json`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/manifest.yaml`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/replication.py`
- `engine/runs/bis_credit_gap_house_price_reversal_oecd_1970_2025/result_card.md`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/chart_data.json`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/coefficients.parquet`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/diagnostics.json`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/manifest.yaml`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/replication.py`
- `engine/runs/bis_credit_gap_low_real_rate_amplifier_panel/result_card.md`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/chart_data.json`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/coefficients.parquet`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/diagnostics.json`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/manifest.yaml`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/replication.py`
- `engine/runs/bis_credit_gap_private_investment_reversal_panel/result_card.md`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/chart_data.json`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/coefficients.parquet`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/diagnostics.json`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/manifest.yaml`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/replication.py`
- `engine/runs/bis_house_price_credit_gap_boom_bust_panel/result_card.md`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/chart_data.json`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/coefficients.parquet`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/diagnostics.json`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/manifest.yaml`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/replication.py`
- `engine/runs/bis_long_horizon_credit_cycle_market_discipline_panel/result_card.md`
- `hypotheses/growth/bis_corporate_dsr_investment_slowdown_panel_1999_2025.yaml`
- `hypotheses/growth/bis_credit_gap_private_investment_reversal_panel.yaml`
- `hypotheses/growth/bis_long_horizon_credit_cycle_market_discipline_panel.yaml`
- `hypotheses/housing/bis_credit_gap_house_price_reversal_oecd_1970_2025.yaml`
- `hypotheses/housing/bis_house_price_credit_gap_boom_bust_panel.yaml`
- `hypotheses/monetary/bis_credit_gap_current_account_twin_deficit_risk.yaml`
- `hypotheses/monetary/bis_credit_gap_dsr_joint_fragility_panel_1999_2025.yaml`
- `hypotheses/monetary/bis_credit_gap_low_real_rate_amplifier_panel.yaml`
- `hypotheses/steelman/bis_corporate_dsr_investment_slowdown_panel_1999_2025.md`
- `hypotheses/steelman/bis_credit_gap_current_account_twin_deficit_risk.md`
- `hypotheses/steelman/bis_credit_gap_dsr_joint_fragility_panel_1999_2025.md`
- `hypotheses/steelman/bis_credit_gap_house_price_reversal_oecd_1970_2025.md`
- `hypotheses/steelman/bis_credit_gap_low_real_rate_amplifier_panel.md`
- `hypotheses/steelman/bis_credit_gap_private_investment_reversal_panel.md`
- `hypotheses/steelman/bis_house_price_credit_gap_boom_bust_panel.md`
- `hypotheses/steelman/bis_long_horizon_credit_cycle_market_discipline_panel.md`
