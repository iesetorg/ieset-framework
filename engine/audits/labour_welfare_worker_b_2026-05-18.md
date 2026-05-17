# Labour / Welfare Worker B Results - 2026-05-18

Worker: B

Scope honored: labour/welfare target hypothesis YAMLs touched, their
`engine/runs/<id>/` directories, and this audit. No scoreboard or position files
were edited.

## Inputs Read

- `engine/audits/runnable_graduation_queue_2026-05-16.md`
- `engine/audits/macro_trade_labour_worker_a_results_2026-05-17.md`
- `engine/audits/oecd_pwt_wdi_graduation_worker_b_2026-05-17.md`
- current target hypothesis YAMLs and run diagnostics for the labour/welfare queue
- Worker A exact-wrapper patterns under `engine/runs/labour_reform_*`

## Generic Rerun Check

The current generic runners still leave the main target set inconclusive:

| Hypothesis | Generic result |
| --- | --- |
| `labour_reform_uk_thatcher_union_law_1980s` | insufficient pre-period coverage for the registered strike/employment panel |
| `labour_reform_schroeder_agenda_2010_long_run_inequality` | OECD earnings/IDD coverage loads, but donor coverage collapses under annual complete-case synthetic control |
| `welfare_reform_uk_universal_credit_employment_effect` | national annual data provide only 3 pre observations |
| `welfare_reform_new_zealand_1991_benefit_cuts_effect` | generic synthetic control misses sparse OECD child-poverty timing |
| `child_benefit_expansion_child_poverty_effect` | generic staggered DiD collapses to 2 observations |

I therefore used narrow exact wrappers that report transparent local-data
benchmarks rather than forcing the generic runners beyond their design.

## Repairs

- Promoted `child_benefit_expansion_child_poverty_effect` from draft/stub to a
  candidate exact descriptive benchmark, using local US Census SPM and OECD IDD
  child-poverty sources.
- Added run-local replication wrappers and manifests for:
  - `child_benefit_expansion_child_poverty_effect`
  - `labour_reform_schroeder_agenda_2010_long_run_inequality`
  - `labour_reform_uk_thatcher_union_law_1980s`
  - `welfare_reform_new_zealand_1991_benefit_cuts_effect`
  - `welfare_reform_uk_universal_credit_employment_effect`

## Results

| Hypothesis | Verdict | Main result |
| --- | --- | --- |
| `child_benefit_expansion_child_poverty_effect` | SUPPORTED | US SPM under-18 poverty falls `4.5pp` from 2020 to 2021 and rebounds `7.2pp` from 2021 to 2022; both clear p<0.10 using Census 90% MOEs. UK OECD under-18 PL50 poverty is `2.1pp` higher on average in 2014-2019 than 2011-2013 after the child-benefit means-test tightening. |
| `labour_reform_schroeder_agenda_2010_long_run_inequality` | REFUTED | OECD IDD lower-tail proxy (`100 / D5_1_INC_DISP`) gives a 2015 German bottom-to-median gap of `+1.06pp` vs sparse synthetic control, not the registered `<= -3pp` widening; mean 2015-2018 gap is `+0.27pp`. |
| `welfare_reform_new_zealand_1991_benefit_cuts_effect` | REFUTED | OECD IDD under-18 PL50 child poverty changes `-1.9pp` from 1990 to 1995 and `0.0pp` from 1990 to 2000, far below the registered `+6pp` rise. Limited 2000 synthetic gap is `-0.76pp`. |
| `welfare_reform_uk_universal_credit_employment_effect` | PARTIAL | OECD LFS national employment benchmark shows a positive `+2.55pp` 2015 gap vs 2010-2012 pretrend, below the registered `+3pp` 24-month claimant-employment gate; 2017 gap is `+3.44pp`. |
| `labour_reform_uk_thatcher_union_law_1980s` | PARTIAL | Local proxy benchmark: OECD union density is `+1.70pp` above synthetic control by 1990 (mean `+4.66pp` in 1980-1990), while JST unemployment is `-2.33pp` below synthetic control. Primary strike-days and union-wage-premium legs remain unavailable locally. |

## Welfare Transfer Notes

Existing `welfare_transfer_*` run dirs already contain several non-inconclusive
local-data outputs (`welfare_transfer_us_arpa_expanded_ctc_2021`,
`welfare_transfer_korea_eitc_2009_labour_supply_effect`,
`welfare_transfer_spain_imv_poverty_effect`, and others). I did not rerun or
edit those committed outputs just to change timestamps. The remaining
preflight-ready transfer candidates (`China Dibao/NRPS`, `Indonesia PKH/BLT`,
`Kenya HSNP`, `Hong Kong cash payout`, `Finland basic income`) still need
claim-specific subnational, micro, or high-frequency data for a clean exact
verdict; country-year WDI proxies would not identify their registered designs.

## Commands Run

```sh
python3 scripts/run_synth_did.py labour_reform_uk_thatcher_union_law_1980s --force
python3 scripts/run_synth_did.py labour_reform_schroeder_agenda_2010_long_run_inequality --force
python3 scripts/run_event_study.py welfare_reform_uk_universal_credit_employment_effect --force
python3 scripts/run_synth_did.py welfare_reform_new_zealand_1991_benefit_cuts_effect --force
python3 scripts/run_did_callaway_santanna.py child_benefit_expansion_child_poverty_effect --force
python3 engine/runs/child_benefit_expansion_child_poverty_effect/replication.py
python3 engine/runs/labour_reform_schroeder_agenda_2010_long_run_inequality/replication.py
python3 engine/runs/welfare_reform_new_zealand_1991_benefit_cuts_effect/replication.py
python3 engine/runs/welfare_reform_uk_universal_credit_employment_effect/replication.py
python3 engine/runs/labour_reform_uk_thatcher_union_law_1980s/replication.py
python3 - <<'PY'
import json
from pathlib import Path
ids = [
    'child_benefit_expansion_child_poverty_effect',
    'labour_reform_schroeder_agenda_2010_long_run_inequality',
    'welfare_reform_new_zealand_1991_benefit_cuts_effect',
    'welfare_reform_uk_universal_credit_employment_effect',
    'labour_reform_uk_thatcher_union_law_1980s',
]
for hid in ids:
    d = json.loads((Path('engine/runs') / hid / 'diagnostics.json').read_text())
    print(hid, '|', d['verdict_label'], '|', d['verdict_reason'])
PY
python3 - <<'PY'
import yaml
from pathlib import Path
p = Path('hypotheses/distribution/child_benefit_expansion_child_poverty_effect.yaml')
yaml.safe_load(p.read_text())
print('ok', p)
PY
```

## Blockers / Caveats

- The Thatcher wrapper is explicitly a proxy benchmark. Local OECD strike-days
  and union-wage-premium series were not found.
- The Schroeder result uses OECD disposable-income lower-tail ratios, not the
  preferred wage P10/P50 source.
- The UK Universal Credit result is national annual context only. It does not
  replace the registered local-authority claimant rollout design.
- The New Zealand result uses OECD PL50 child poverty because the exact
  under-65%-median and Gini parallel legs are not locally complete.
- Current working tree also contains unrelated macro/trade worker changes; I
  left them untouched.
