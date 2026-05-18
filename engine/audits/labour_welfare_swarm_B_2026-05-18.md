# Labour/Welfare Swarm B Audit - 2026-05-18

Worker B scope was limited to labour/welfare/distribution hypotheses and matching
`labour_*`, `welfare_*`, `transfer_*`, and `child_*` run artifacts. I did not edit
scoreboard/positions files, the 2026-05-17T2317 fetch manifests, or the daily
rate-limited backfill audits that were dirty before this pass.

## Selection

I selected eight welfare/distribution candidates with local data sufficient for
preflight-ready or repairable verdicts. The repairs prefer exact local-data
benchmarks with explicit missing-variable gates over timestamp reruns.

| Hypothesis | Verdict | Exact local test |
| --- | --- | --- |
| `welfare_transfer_brazil_bolsa_familia_phase2_effect` | SUPPORTED | WDI poverty/Gini phase-1 vs phase-2 diminishing-return benchmark. |
| `welfare_transfer_indonesia_pkh_blt_2007_2022` | PARTIAL | WDI poverty, Gini, and secondary-enrolment national PKH window; BLT smoothing missing. |
| `welfare_transfer_china_dibao_rural_pension_2009` | PARTIAL | WDI 2010-2014 poverty/Gini sign check plus GDP-per-capita growth confound. |
| `welfare_transfer_mexico_prospera_phaseout_2019` | REFUTED | WDI 2018-2022 and 2018-2024 poverty gate moves opposite the registered claim. |
| `welfare_transfer_argentina_auh_2009_child_poverty_effect` | REFUTED | WDI extreme-poverty proxy misses the registered 8pp child-poverty gate. |
| `welfare_transfer_south_africa_social_grants_long_run` | PARTIAL | WDI long-run poverty/Gini magnitude check; grant-intensity/fiscal-placebo gates missing. |
| `welfare_transfer_korea_eitc_2009_labour_supply_effect` | PARTIAL | WDI national female-LFP proxy clears the 2-4pp band; low-income RD sample missing. |
| `welfare_transfer_us_arpa_expanded_ctc_2021` | WEAKENED | US Census annual SPM under-18 poverty onset/expiration gates clear; CPSP monthly and LFP gates missing. |

## Verdict Notes

- Brazil: phase-2 poverty drop was 0.1pp vs phase-1 8.7pp; Gini rose 0.6pp
  after a 3.9pp phase-1 drop, supporting diminishing returns.
- Indonesia: poverty fell 30.2pp and secondary enrolment rose 13.9pp over the
  PKH-era national window, but the short-run BLT consumption-smoothing outcome
  is not present locally.
- China: poverty fell 16.0pp over 2010-2014, but real GDP per capita rose 39.4%,
  so local data cannot separate transfer rollout from growth.
- Mexico: extreme poverty fell 1.6pp by 2022 and 2.3pp by 2024 from the 2018
  baseline, refuting the registered post-phaseout +3pp poverty-rise direction.
- Argentina: the local WDI poverty proxy fell only 1.3pp by 2013, below the
  registered 8pp child-poverty gate. This is a proxy-gate refutation because
  harmonised child-poverty microdata are not local.
- South Africa: poverty fell 30.5pp and Gini fell 3.7pp over 2000-2022, but the
  result remains partial without SASSA coverage, fiscal-balance, and placebo
  inference gates.
- Korea: national female LFP rose 2.3pp from 2009 to 2014, matching the broad
  hypothesis band, but the registered low-income married-women discontinuity
  design is not local.
- US ARPA CTC: Census annual SPM child poverty fell 4.5pp from 2020 to 2021 and
  rebounded 7.2pp from 2021 to 2022. The annual poverty gates clear, but the
  preferred monthly CPSP and parental-LFP checks are missing.

## Artifacts

Each repaired run has `replication.py`, `manifest.yaml`, `diagnostics.json`, and
`result_card.md` under its run directory. Shared exact-run logic lives in
`engine/runs/welfare_worker_b_exact.py`.

## Commands Run

```sh
python3 -m py_compile engine/runs/welfare_worker_b_exact.py engine/runs/welfare_transfer_brazil_bolsa_familia_phase2_effect/replication.py engine/runs/welfare_transfer_indonesia_pkh_blt_2007_2022/replication.py engine/runs/welfare_transfer_china_dibao_rural_pension_2009/replication.py engine/runs/welfare_transfer_mexico_prospera_phaseout_2019/replication.py engine/runs/welfare_transfer_argentina_auh_2009_child_poverty_effect/replication.py engine/runs/welfare_transfer_south_africa_social_grants_long_run/replication.py engine/runs/welfare_transfer_korea_eitc_2009_labour_supply_effect/replication.py engine/runs/welfare_transfer_us_arpa_expanded_ctc_2021/replication.py
python3 engine/runs/welfare_transfer_brazil_bolsa_familia_phase2_effect/replication.py
python3 engine/runs/welfare_transfer_indonesia_pkh_blt_2007_2022/replication.py
python3 engine/runs/welfare_transfer_china_dibao_rural_pension_2009/replication.py
python3 engine/runs/welfare_transfer_mexico_prospera_phaseout_2019/replication.py
python3 engine/runs/welfare_transfer_argentina_auh_2009_child_poverty_effect/replication.py
python3 engine/runs/welfare_transfer_south_africa_social_grants_long_run/replication.py
python3 engine/runs/welfare_transfer_korea_eitc_2009_labour_supply_effect/replication.py
python3 engine/runs/welfare_transfer_us_arpa_expanded_ctc_2021/replication.py
```

The wrapper runs emitted harmless `pyarrow` sysctl warnings in this macOS
sandbox, then completed and wrote artifacts.

## Blocked Or Deferred

- `welfare_reform_prwora_single_mother_employment`: local BLS data did not expose
  the necessary 1990s single-mother LFP/employment panel.
- `transfer_expansion_work_incentive_long_run`: promising but needs a narrower
  transfer-expansion design and labour-supply series than the local inventory
  exposed during this pass.
- Finland/Stockton/Kenya-type cash-transfer candidates: exact RCT or monthly
  household microdata were not local, so I did not force proxy reruns.
- `uk_real_wage_stagnation_2008_present_decomposition`: promising labour lane,
  but the run id starts `uk_*`, outside the run-id ownership boundaries for this
  pass.
- `welfare_reform_uk_universal_credit_employment_effect`: already had an exact
  local OECD-LFS wrapper/result card, so I left it unchanged.

## Churn And Restore Notes

No scoreboard, positions, hypothesis YAML, off-limits data manifest, or
2026-05-17T2317 audit files were edited. No restores are recommended from Worker
B's lane. The only generated artifacts are the run outputs and this audit.
