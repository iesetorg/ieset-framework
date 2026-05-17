# Macro / Monetary Worker A Results - 2026-05-18

Scope: repair-led macro/monetary reruns using local FRED/JST/Shiller/IMF data only.

Inputs read:

- `engine/audits/runnable_graduation_queue_2026-05-16.md`
- `engine/audits/macro_trade_labour_worker_a_results_2026-05-17.md`
- `engine/audits/graduation_data_pack_macro_trade_labour_2026-05-16.md`
- `scripts/run_descriptive.py`
- `scripts/run_event_study.py`
- `scripts/run_local_projections.py`
- commit boundary: `git show --name-only --oneline --no-renames 980b0110`

## Candidate Selection

I avoided hypotheses already graduated in commit `980b0110` except for reading style and local methodology patterns. That excludes the already-graduated `friedman_schwartz_great_depression_monetary_cause` and `fed_qt_balance_sheet_unwind_2022_2025_market_response` results.

Targeted candidates:

| Hypothesis | Prior state | Repair / rerun type |
| --- | --- | --- |
| `great_depression_over_accumulation_vs_monetary_cause` | `INCONCLUSIVE_DATA_PENDING` | exact JST + Shiller proxy wrapper |
| `fed_2022_rate_cycle_inflation_response_lag` | `INCONCLUSIVE_DATA_PENDING` | exact CPI decomposition upper-bound wrapper |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | existing `SUPPORTED` artifact | reran existing replication wrapper |
| `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | existing `WEAKENED` artifact | reran existing replication wrapper |

No scoreboard or positions files were edited.

## Results

| Hypothesis | Verdict | Main result |
| --- | --- | --- |
| `financial_fed_reverse_repo_facility_usage_2021_2024` | SUPPORTED | ON RRP peaked at `$2,553.716bn` on 2022-12-30 and fell `$2,314.330bn` by the 2024Q3 low. |
| `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | WEAKENED | USA core-CPI and inflation-expectations gates clear, but the local gate is USA-only and the 2020 balance-sheet/GDP max is `29.626%`, just below the 30% claim threshold. |
| `fed_2022_rate_cycle_inflation_response_lag` | PARTIAL | Headline CPI YoY fell `5.769pp` from 2022-06 to 2024-12; the headline-minus-core non-core wedge explains `55.3%`, while treating all core disinflation as a generous Fed-sensitive upper bound gives `44.7%`. Shadow-rate, wage, GSCPI, and narrative-IV inputs are not loaded, so this does not graduate to full support. |
| `great_depression_over_accumulation_vs_monetary_cause` | PARTIAL | Shiller earnings yield falls `41.5%` from 1923 to 1929, clearing the proxy profitability-decline gate, but direct profit-rate/capital-output data are missing; JST investment share is flat/slightly down from 1925 to 1929 and the competing monetary-contraction gate also clears (`money -28.48` log-ppt, nominal GDP `-45.34%`, real GDP `-30.76%`, 1929-1933). |

## Commands Run

```sh
python3 engine/runs/fed_2022_rate_cycle_inflation_response_lag/replication.py
python3 engine/runs/great_depression_over_accumulation_vs_monetary_cause/replication.py
python3 engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024/replication.py
python3 engine/runs/central_bank_balance_sheet_cpi_decoupling_panel_2008_2020/replication.py
python3 - <<'PY'
import json
from pathlib import Path
ids = [
    'great_depression_over_accumulation_vs_monetary_cause',
    'financial_fed_reverse_repo_facility_usage_2021_2024',
    'fed_2022_rate_cycle_inflation_response_lag',
    'central_bank_balance_sheet_cpi_decoupling_panel_2008_2020',
]
for hid in ids:
    d=json.loads((Path('engine/runs')/hid/'diagnostics.json').read_text())
    print(hid, d.get('verdict_label'), d.get('verdict_reason'))
PY
git status --short
git diff -- engine/runs/great_depression_over_accumulation_vs_monetary_cause \
  engine/runs/fed_2022_rate_cycle_inflation_response_lag \
  engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024 \
  engine/runs/central_bank_balance_sheet_cpi_decoupling_panel_2008_2020
```

## Blockers / Caveats

- `fed_2022_rate_cycle_inflation_response_lag`: local data support a descriptive CPI component upper-bound check, not the registered Romer-Romer / shadow-rate causal decomposition. Missing: `fred:WUXIASHADOWRATE`, `fred:FRBATLWGT12MMUMHWGO`, NY Fed `GSCPI`, and narrative monetary-shock inputs.
- `great_depression_over_accumulation_vs_monetary_cause`: no direct local Duménil-Levy/Shaikh profit-rate or capital-output series is loaded. The wrapper uses JST investment share and Shiller equity earnings/dividend yields as proxies and reports the competing JST monetary channel explicitly.
- `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`: current artifact remains USA-only; Japan/ECB/BoE core-CPI and 5y5y gates are not locally loaded.
- The worktree contains unrelated dirty files from other lanes; they were not edited by this worker.
