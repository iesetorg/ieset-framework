# Worker E HERITAGE 16-35 Panel Graduation Audit

Worker: E
Date: 2026-05-19
Scope: selected ranks 16-35 from `engine/queue_heritage_market_graduation.yaml`; only new strengthened run variants under `engine/runs/heritage_*_wgi_*_panel` plus this audit.

## Guardrail

These inputs are post-estimation HERITAGE candidate screens. None of the new artifacts is scoreboard eligible. Each new run records `scoreboard_eligible: false` and `methodology_gate: candidate_screen_graduation_artifact_not_scoreboard_evidence`. Supported panel artifacts still require a matching pre-registration/spec audit before any scoreboard promotion.

## Selection

Selected candidates with loadable time-varying WGI/WDI proxy panels and loadable WDI outcomes. Estimator for every run:

- Outcome on lagged one-year proxy plus log PPP GDP per capita.
- Country and year fixed effects.
- Country-clustered standard errors.
- Leave-one-region-out robustness using Heritage region labels.
- Support gate: expected sign and p <= 0.10.

## Graduated Artifacts

| Queue rank | Strengthened run id | Proxy -> outcome | Verdict | Panel result | Leave-one-region-out | Status |
| ---: | --- | --- | --- | --- | --- | --- |
| 16 | `heritage_business_freedom_electricity_access_wgi_rq_panel` | WGI regulatory quality -> electricity access | PARTIAL | beta=-1.327, p=0.403, n=4,474, countries=194 | 0/5 expected sign | Blocker: candidate cross-section does not survive country/year FE. |
| 17 | `heritage_business_freedom_inflation_rate_wgi_rq_panel` | WGI regulatory quality -> CPI inflation | PARTIAL | beta=-3.838, p=0.217, n=4,185, countries=187 | 5/5 expected sign | Directional prep artifact, not decisive. |
| 18 | `heritage_business_freedom_under5_mortality_wgi_rq_panel` | WGI regulatory quality -> under-5 mortality | PARTIAL | beta=-5.083, p=0.128, n=4,370, countries=187 | 4/5 expected sign | Directional prep artifact, just above alpha. |
| 20 | `heritage_economic_freedom_high_tech_exports_wgi_composite_panel` | WGI RQ/RL/CC composite -> high-tech exports share | PARTIAL | beta=1.920, p=0.165, n=2,494, countries=180 | 5/5 expected sign | Directional prep artifact, not decisive. |
| 22 | `heritage_economic_freedom_life_expectancy_wgi_composite_panel` | WGI RQ/RL/CC composite -> life expectancy | SUPPORTED | beta=1.008, p=0.022, n=4,627, countries=195 | 5/5 expected sign | Strongest graduation candidate; still not scoreboard eligible. |
| 28 | `heritage_business_freedom_private_consumption_pc_wgi_rq_panel` | WGI regulatory quality -> log private consumption pc | SUPPORTED | beta=0.0582, p=0.026, n=3,603, countries=170 | 5/5 expected sign | Strong graduation candidate; still not scoreboard eligible. |
| 32 | `heritage_property_rights_high_tech_exports_wgi_rl_panel` | WGI rule of law -> high-tech exports share | PARTIAL | beta=1.287, p=0.417, n=2,494, countries=180 | 5/5 expected sign | Directional prep artifact, too imprecise. |

## Files Created

- `engine/runs/heritage_business_freedom_electricity_access_wgi_rq_panel/`
- `engine/runs/heritage_business_freedom_inflation_rate_wgi_rq_panel/`
- `engine/runs/heritage_business_freedom_under5_mortality_wgi_rq_panel/`
- `engine/runs/heritage_economic_freedom_high_tech_exports_wgi_composite_panel/`
- `engine/runs/heritage_economic_freedom_life_expectancy_wgi_composite_panel/`
- `engine/runs/heritage_business_freedom_private_consumption_pc_wgi_rq_panel/`
- `engine/runs/heritage_property_rights_high_tech_exports_wgi_rl_panel/`

Each run directory contains `replication.py`, `manifest.yaml`, `diagnostics.json`, `result_card.md`, and `chart_data.json`. The first run directory also contains the shared Worker E helper `panel_proxy_runner.py`.

## Blockers And Next Steps

- Rank 16 is blocked from promotion: the panel sign flips after country/year FE and log-income control.
- Ranks 17, 18, 20, and 32 are useful prep artifacts but need either a tighter pre-registered design, longer outcome windows, alternate non-HERITAGE proxy choices, or event shocks before a real support claim.
- Ranks 22 and 28 are the cleanest candidates for a subsequent explicit hypothesis YAML/pre-registration pass.
- No original candidate-screen run, hypothesis YAML, scoreboard page, position file, or May 17 daily-backfill file was edited by Worker E.

## Commands

- `python3 engine/runs/heritage_business_freedom_electricity_access_wgi_rq_panel/replication.py`
- `python3 engine/runs/heritage_business_freedom_inflation_rate_wgi_rq_panel/replication.py`
- `python3 engine/runs/heritage_business_freedom_under5_mortality_wgi_rq_panel/replication.py`
- `python3 engine/runs/heritage_economic_freedom_high_tech_exports_wgi_composite_panel/replication.py`
- `python3 engine/runs/heritage_economic_freedom_life_expectancy_wgi_composite_panel/replication.py`
- `python3 engine/runs/heritage_business_freedom_private_consumption_pc_wgi_rq_panel/replication.py`
- `python3 engine/runs/heritage_property_rights_high_tech_exports_wgi_rl_panel/replication.py`
- `python3 -m py_compile` on the shared helper and all seven `replication.py` wrappers.
- JSON/YAML parse and gate check over all seven generated runs: `validated 7 runs`.
- ASCII scan over this audit plus generated run artifacts: `ascii-ok 37 files`.

PyArrow emitted sandbox CPU-cache `sysctlbyname` warnings during parquet reads, but all seven wrappers exited 0 and wrote complete artifacts.
