# BIS Batch 04 Wave Results — 2026-05-12

This audit tracks the first Austrian/BIS factory push from Batch 04 of `new_data_hypothesis_batches_02_04_2026-05-12.md`.

## What Was Added

- New promotion runner: `scripts/promote_bis_batch04_wave_2026_05_12.py`
- 20 new hypothesis YAML specs.
- 20 new steelman files.
- 20 new run directories with `replication.py`, `result_card.md`, `diagnostics.json`, `manifest.yaml`, `coefficients.parquet`, and `chart_data.json`.

## Verdict Tally

| Verdict | Count |
|---|---:|
| `SUPPORTED` | 1 |
| `PARTIAL` | 8 |
| `REFUTED` | 9 |
| `INCONCLUSIVE_DATA_PENDING` | 2 |

## Results

### Wave 1

| Hypothesis | Verdict | Reason |
|---|---|---|
| `bis_credit_gap_dsr_joint_crisis_risk_panel_1999_2025` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_household_dsr_consumption_slowdown_panel_1999_2025` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_corporate_credit_boom_investment_slowdown_panel_1970_2025` | `INCONCLUSIVE_DATA_PENDING` | Insufficient coverage for the predeclared gate. |
| `bis_credit_gap_current_account_interaction_panel_1970_2025` | `SUPPORTED` | Regression and raw contrast both clear the predeclared gates. |
| `bis_credit_gap_property_price_interaction_panel_1970_2025` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_reer_appreciation_export_growth_panel_1964_2026` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_reer_appreciation_industrial_share_panel_1964_2026` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_reer_misalignment_current_account_repair_panel_1964_2026` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_reer_devaluation_inflation_tradeoff_panel_1964_2026` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_reer_volatility_investment_drag_panel_1964_2026` | `INCONCLUSIVE_DATA_PENDING` | Insufficient coverage for the predeclared gate. |

### Wave 2

| Hypothesis | Verdict | Reason |
|---|---|---|
| `bis_credit_gap_unemployment_lag_panel_1970_2025` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_credit_gap_consumption_slowdown_panel_1970_2025` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_credit_gap_private_investment_slowdown_panel_1970_2025` | `INCONCLUSIVE_DATA_PENDING` | Insufficient coverage for the predeclared gate. |
| `bis_dsr_current_account_deficit_unemployment_panel_1999_2025` | `PARTIAL` | One of the regression or raw-contrast gates clears, but not both. |
| `bis_dsr_house_price_boom_reversal_panel_1999_2025` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_reer_volatility_export_drag_panel_1964_2026` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_reer_depreciation_current_account_repair_panel_1964_2026` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_reer_appreciation_inflation_relief_panel_1964_2026` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_credit_gap_export_growth_drag_panel_1970_2025` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |
| `bis_credit_gap_manufacturing_share_drag_panel_1970_2025` | `REFUTED` | Neither the regression nor raw-contrast gate clears. |

## Interpretation

The strongest supported result is the interaction claim: credit-gap stress is much more dangerous when paired with current-account deficit conditions. Several Austrian-compatible claims are only partial: credit gaps predict later unemployment and consumption weakness in at least one gate, but not cleanly across both regression and raw contrasts. The REER channel is much weaker than the broad Austrian/price-signal framing would imply in these specifications: export, current-account repair, volatility/export drag, and inflation-relief variants are mostly refuted.

The two inconclusive tests are not ideological misses; they failed coverage gates. They should be retried with a lower-frequency annual design or better investment/volatility construction before scoreboard conversion.

## Verification

- `python3 -c "import ast, pathlib; ast.parse(pathlib.Path('scripts/promote_bis_batch04_wave_2026_05_12.py').read_text())"`: passed.
- `python3 scripts/validate_scope_alignment.py`: 2313 pass, 0 errors.
- `python3 scripts/validate_specs.py 2>&1 | rg <new BIS ids>`: no matches after generator repair, meaning the new 10 specs are not among the schema errors. The full repo still has pre-existing validation errors unrelated to this wave.
