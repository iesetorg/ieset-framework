# Macro / Trade / Labour Worker A Results - 2026-05-17

Scope: repair-led reruns after the current generic preflight queue was exhausted.

Inputs read:

- `engine/audits/runnable_graduation_queue_2026-05-16.md`
- `engine/audits/graduation_data_pack_macro_trade_labour_2026-05-16.md`
- `engine/audits/uncommitted_ready_hypotheses_2026-05-16.md`
- current same-day queue audit `engine/audits/graduation_high_quality_batch7_2026-05-17.md`
- generic runners under `scripts/run_*.py`

## Candidate Selection

The stricter preflight now reports only two generic inconclusive candidates, and both are known false positives:

- `high_income_escape_market_openness_1950_2024`: listwise observations collapse to 8.
- `zimbabwe_land_reform_cause_decomposition`: listwise observations collapse to 0.

I therefore selected candidates where local raw data existed but the generic annual/panel runner was the blocker:

| Hypothesis | Lane | Repair type |
| --- | --- | --- |
| `friedman_schwartz_great_depression_monetary_cause` | macro/monetary | exact JST annual gate; YAML threshold sharpened |
| `fed_qt_balance_sheet_unwind_2022_2025_market_response` | macro/monetary | daily FRED event wrapper |
| `corbyn_manifesto_capital_flight_prediction` | labour/capital markets | daily BoE/FRED event wrapper; YAML threshold sharpened |
| `labour_reform_canada_1990s_ui_reform_nairu` | labour | JST unemployment synthetic-control benchmark |
| `labour_reform_sweden_1990s_employment_recovery` | labour | JST unemployment synthetic-control benchmark |
| `macron_labour_tax_employment_distribution` | labour | national WDI/OECD exact benchmark; YAML threshold sharpened |

## Results

| Hypothesis | Verdict | Main result |
| --- | --- | --- |
| `friedman_schwartz_great_depression_monetary_cause` | SUPPORTED | JST 1929-1933: money `-28.48` log-ppt, nominal GDP `-45.34%`, real GDP `-30.76%`. |
| `corbyn_manifesto_capital_flight_prediction` | SUPPORTED | 2017/2019 manifesto windows show no >2-sigma adverse GBP or gilt move; worst GBP 3d change `-0.031%`, gilt windows both down over 3 trading days. |
| `fed_qt_balance_sheet_unwind_2022_2025_market_response` | REFUTED | Five pinned QT events have cumulative 10y term-premium response `-0.96bp`; per-$T runoff effect `-0.58bp/$T`, failing the positive reverse-QE gate. |
| `labour_reform_canada_1990s_ui_reform_nairu` | REFUTED | JST unemployment gap vs synthetic control is `+3.67pp` mean in 1990-2000 and `+2.94pp` by 2000, opposite the claim. |
| `labour_reform_sweden_1990s_employment_recovery` | PARTIAL | JST unemployment benchmark is favorable (`-5.47pp` mean gap), but placebo `p=0.333` misses the registered inference gate. |
| `macron_labour_tax_employment_distribution` | PARTIAL | 2019 unemployment is `-2.51pp` below 2010-2016 pretrend, but disposable-income Gini rises only `+0.001`, below the `+0.005` distributional-cost gate. |

## Commands Run

```sh
python3 scripts/rerun_preflight_ready_inconclusive.py
python3 scripts/run_panel_fe.py high_income_escape_market_openness_1950_2024 --force
python3 scripts/run_panel_fe.py zimbabwe_land_reform_cause_decomposition --force
git restore -- engine/runs/high_income_escape_market_openness_1950_2024/diagnostics.json engine/runs/high_income_escape_market_openness_1950_2024/result_card.md engine/runs/zimbabwe_land_reform_cause_decomposition/diagnostics.json engine/runs/zimbabwe_land_reform_cause_decomposition/result_card.md
python3 engine/runs/friedman_schwartz_great_depression_monetary_cause/replication.py
python3 engine/runs/corbyn_manifesto_capital_flight_prediction/replication.py
python3 engine/runs/fed_qt_balance_sheet_unwind_2022_2025_market_response/replication.py
python3 engine/runs/labour_reform_canada_1990s_ui_reform_nairu/replication.py
python3 engine/runs/labour_reform_sweden_1990s_employment_recovery/replication.py
python3 engine/runs/macron_labour_tax_employment_distribution/replication.py
python3 - <<'PY'
import json
from pathlib import Path
ids = [
    'friedman_schwartz_great_depression_monetary_cause',
    'corbyn_manifesto_capital_flight_prediction',
    'fed_qt_balance_sheet_unwind_2022_2025_market_response',
    'labour_reform_canada_1990s_ui_reform_nairu',
    'labour_reform_sweden_1990s_employment_recovery',
    'macron_labour_tax_employment_distribution',
]
for hid in ids:
    d = json.loads((Path('engine/runs') / hid / 'diagnostics.json').read_text())
    print(hid, d['verdict_label'], d['verdict_reason'])
PY
python3 - <<'PY'
import yaml
from pathlib import Path
for p in [
    'hypotheses/monetary/friedman_schwartz_great_depression_monetary_cause.yaml',
    'hypotheses/labour/corbyn_manifesto_capital_flight_prediction.yaml',
    'hypotheses/labour/macron_labour_tax_employment_distribution.yaml',
]:
    yaml.safe_load(Path(p).read_text())
    print('ok', p)
PY
```

## Blockers / Caveats

- No scoreboard or positions files were edited.
- Generic preflight reruns remain exhausted; the two residual candidates are estimand-blocked, not source-blocked.
- `productivity_compensation_decoupling_post_1973` remains intentionally skipped because local BLS PRS vintages lack the required 1973/2019 endpoints.
- New Zealand ECA was not run because JST has no `NZL` unemployment history in the local vintage, while WDI unemployment starts too late for a pre-1991 synthetic-control window.
- Canada and Sweden are national JST unemployment benchmarks. The Canada regional frequent-claimant leg and Sweden SEK-channel partialling still need richer local inputs before a final public-grade design.
- Fed QT result grades the five date-pinned events; the YAML's `2025-01` event is not date-pinned locally, and the MBS OAS leg is still missing. The refutation is driven by the registered term-premium direction gate.
