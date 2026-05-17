# OECD/PWT/WDI Graduation Worker B Audit - 2026-05-17

Worker: B

Scope honored: OECD/PWT/WDI-oriented hypothesis YAMLs, their `engine/runs/<id>/`
directories, and this audit file. No scoreboard or position files were edited.

## Inputs Read

- `engine/audits/graduation_data_pack_oecd_pwt_2026-05-16.md`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- `engine/audits/runnable_graduation_queue_2026-05-16.md`
- `scripts/run_panel_fe.py`
- `scripts/run_event_study.py`
- `scripts/run_descriptive.py`
- relevant OECD/PWT/WDI hypothesis YAMLs and current run diagnostics

## Local Vintage Checks

Confirmed existing local vintages for the patched sources:

- OECD IMD migration education/employment bridge:
  `data/vintages/oecd/OECD.ELS.IMD_DSD_MIG_DF_MIG_EMP_EDU_1.0@2026-05-12T120747Z.parquet`
- OECD Productivity Database:
  `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`
- PWT aliases already load locally, including:
  `pwt:rgdpo_emp -> pwt:rgdpo_per_emp`, `pwt:ccon_pop`, `pwt:csh_i`,
  `pwt:csh_x`, and `pwt:rconna`.

## Spec Alias Repairs

Patched only source tokens that were stale against already-landed local vintages:

- `demo_migration_inflows_wages_skill_split`:
  `oecd:OECD.ELS.IMM,DSD_DIOC@DF_DIOC,1.0` -> `oecd:OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0`
- `demo_canada_points_system_immigration`:
  same legacy DIOC token -> current OECD IMD education/employment vintage
- `demo_australia_high_skill_migration`:
  same legacy DIOC token -> current OECD IMD education/employment vintage
- `oecd_product_market_deregulation_tfp_panel`:
  `oecd:DSD_PDB@DF_PDB_PT` -> `oecd:DSD_PDB`

Mapping caveat: the generic runner reduces SDMX cubes to country-year means.
These bridges make the specs runnable against local vintages but are not a
measure-specific OECD slice. Treat the results as graduation/triage outputs,
not scoreboard-ready causal evidence.

## Runs And Verdicts

| Hypothesis | Result | Notes |
| --- | --- | --- |
| `demo_migration_inflows_wages_skill_split` | `PARTIAL` | Graduated from data-pending. `high_skill_migrant_share` loaded from OECD IMD; PanelOLS coefficient `-0.001643`, `p=0.809`, `n=87`, `17` countries. |
| `demo_canada_points_system_immigration` | `INCONCLUSIVE_DATA_PENDING` | All variables now load, but `points_system_indicator` has no within-country variation under country fixed effects. Needs descriptive/cross-sectional premium test or event design. |
| `demo_australia_high_skill_migration` | `INCONCLUSIVE_DATA_PENDING` | All variables now load, but `skill_stream_share` has no within-country variation under country fixed effects. Needs single-country ITS/descriptive design or a real time-varying skill-stream series. |
| `oecd_product_market_deregulation_tfp_panel` | `INCONCLUSIVE_DATA_PENDING` | PWT, WDI, PMR, and PDB proxy all load; blocker is now design/sample: `oecd_pmr_overall_index` has no within-country variation under country FE in the usable PMR slice. |

## Nearby Candidates Not Patched

- `uk_real_wage_stagnation_2008_present_decomposition`: PDB alias can load, but
  the current spec still collapses to 21 observations after listwise deletion
  and uses a placeholder wage source. Held for design/source repair.
- `industrial_concentration_labour_share_link`: PDB proxy can load, but the
  registered concentration treatments are still `derived:bea_compustat_*`
  blockers. Held.
- `state_owned_enterprise_share_growth_plateau`,
  `industrial_policy_without_exit_discipline_failure`, and
  `protected_infant_industries_fail_to_mature`: `pwt:rgdpo_emp` already bridges
  to `pwt:rgdpo_per_emp`, but constructed treatment/manual coding blockers
  remain.
- OECD-STAN tokens were not patched. The local STAN vintage is useful for
  value-added/employment/hour proxies, but it does not establish literal TFP
  measures. `oecd_stan:manufacturing_tfp` and `oecd_stan:tfp_growth` need a
  documented proxy decision or a different source.

## Validation Commands

Executed:

```bash
python3 scripts/run_panel_fe.py demo_migration_inflows_wages_skill_split
python3 scripts/run_panel_fe.py demo_canada_points_system_immigration
python3 scripts/run_panel_fe.py demo_australia_high_skill_migration
python3 scripts/run_panel_fe.py oecd_product_market_deregulation_tfp_panel
```

Diagnostics inspected:

```bash
sed -n '1,220p' engine/runs/demo_migration_inflows_wages_skill_split/diagnostics.json
sed -n '1,220p' engine/runs/demo_canada_points_system_immigration/diagnostics.json
sed -n '1,220p' engine/runs/demo_australia_high_skill_migration/diagnostics.json
sed -n '1,220p' engine/runs/oecd_product_market_deregulation_tfp_panel/diagnostics.json
```

## Blockers

- Generic `panel_fe` is not valid for country-constant treatment indicators
  under country fixed effects. This blocks the Canada points-system,
  Australia skill-stream, and PMR usable-slice reruns.
- OECD IMD migration and OECD PDB aliases are local-vintage bridges, not final
  measure-specific slices.
- No new data were fetched.
- Scoreboard/position mapping should wait for measure-specific slicing or
  design conversion; no scoreboard or position edits were made here.
