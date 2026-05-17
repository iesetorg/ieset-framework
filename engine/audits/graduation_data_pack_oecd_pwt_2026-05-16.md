# Graduation Data Pack - OECD/PWT/OECD-STAN

Date: 2026-05-16

Lane: F1 - OECD/PWT/OECD-STAN data source pack.

Write target only: `engine/audits/graduation_data_pack_oecd_pwt_2026-05-16.md`.

No data were fetched and no existing source, manifest, run, or hypothesis files were edited.

## Inputs Read

- `engine/agent_briefs/graduation_repair_swarm_2026-05-16.md`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- `data/fetchers/publishers.yaml`
- `data/fetchers/oecd.py`
- `data/fetchers/oecd_pmr.py`
- `data/fetchers/pwt.py`
- `data/fetchers/__init__.py`
- `data/manifests/baseline_pull.yaml`
- `data/manifests/coverage.derived.yaml`
- relevant OECD/PWT/STAN vintages and run diagnostics under `data/vintages/` and `engine/runs/`
- local OECD helper scripts: `scripts/discover_oecd_sdmx_support_2026_05_12.py`, `scripts/promote_oecd_pdb_batch03_2026_05_12.py`, `scripts/generate_oecd_labour_wave.py`, `scripts/promote_welfare_labour_minwage_batches_07_09_a4_2026_05_12.py`

## Executive Ranking

The broad graduation plan reports unresolved source-token references of `OECD=196`, `PWT=17`, and `OECD STAN=13`. Current run diagnostics show that many headline PWT/OECD PDB tokens are already locally available; the graduation blocker is now mostly alias/source-token alignment, not raw acquisition.

Feasibility tiers:

- `A`: ready fetcher and clean command, or data already local and only alias wiring is needed.
- `B`: ready generic fetcher, but dataflow/version or measure filters need verification.
- `C`: local data or shortcut exists, but source publisher/series semantics are wrong or a derived variable is required.
- `D`: no registered ready publisher/fetcher or manual/API constraint blocks normal fetching.

| Rank | Source/action | Current blocker unlocks | Broader source refs | Class | Feasibility | Diagnosis |
| ---: | --- | ---: | ---: | --- | --- | --- |
| 1 | `oecd:DSD_EARN@DF_EARN_LFS` | 10 | 10+ | ready fetcher plus missing/partial vintage | A/B | Biggest live blocker. Existing OECD earnings vintages are wage-gap tables, not the broad real-wage/low-pay panel most labour reform specs need. |
| 2 | `oecd_stan:*` alias pack (`manufacturing_tfp`, `gdp_per_hour_worked`, `tfp_growth`, sector value-added tokens) | 10-11 | 13 | missing publisher/source-token problem | C/D | `oecd_stan` is not registered in `publishers.yaml`; generic `oecd` has a `STAN` shortcut and one local `data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@...` file. STAN has value added, employment, hours, capital stock, not literal TFP. |
| 3 | `pwt:rgdpo_emp` | 4 | 4 | alias problem | A | Should map to existing/supported `pwt:rgdpo_per_emp`. |
| 4 | `pwt:rnna` | 4 | 4 | ready PWT pseudo-series | A | Fetcher supports `rnna`; no current vintage found. Manual PWT file and `pwt_full` are local. |
| 5 | `oecd:OECD.SDD.STES,DSD_KEI@DF_KEI,4.0` | 4 | 5 | old dataflow/source-token problem | B/C | Specs cite STES/KEI v4 for short rates/output-gap controls; local/fetcher support points to `OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0`. |
| 6 | `oecd:DSD_IDD@DF_IDD` | 3 | 8 | ready fetcher/alias | A | IDD exists locally under full OECD WISE names; short token aliasing should unlock elderly poverty/gini specs. |
| 7 | `oecd:DSD_PENSIONS@DF_PENSIONS_REPL_RATE` | 3 | 3 | ready fetcher/alias | A/B | Shortcut exists; no local replacement-rate vintage found in current OECD directory. |
| 8 | `oecd:OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0` | 3 | 6 | ready fetcher/local vintage | A | EPL fallback workbook works and local vintages exist; blockers are stale wiring. |
| 9 | `oecd:OECD.ELS.IMM,DSD_DIOC@DF_DIOC,1.0` | 3 | 3 | dataflow/version risk | B/C | Existing OECD migration vintages use `OECD.ELS.IMD` dataflows; raw `IMM/DIOC` may be legacy. |
| 10 | `oecd:STSIND4_PRODMAN` | 3 | 3 | legacy source-token problem | C | Likely old STAN/short-term industrial production token. Needs catalogue confirmation or STAN/NAMAIN substitute. |
| 11 | `oecd:DSD_LFS@DF_LFS_INDIC` | 2 | 6 | ready/local vintage | A | Existing `DSD_LFS_DF_LFS_INDIC@...` vintage can be wired. |
| 12 | `oecd:DSD_LFS@DF_LFS_TEMP` | 2 | 2 | ready fetcher | B | Generic SDMX should fetch if the dataflow is still published. |
| 13 | `oecd:DSD_LFS@DF_LFS_UNION` / `oecd:DSD_TUD@DF_TUD` | 2 | 6+ | alias problem | A | Union density and collective bargaining already exist as `DSD_TUD_CBC` vintages. |
| 14 | `oecd:OECD.ELS.EMP,DSD_LMS@DF_LMS,1.0` | 2 | 4 | ready fetcher | B | Employment/labour-market status panel; needs fetch and loader filters. |
| 15 | `oecd:OECD.ELS.EMP,DSD_LMS@DF_LMS_DURATION,1.0` | 2 | 3 | ready fetcher | B | Duration panel; likely fetchable but not locally present. |
| 16 | `oecd:OECD.ELS.SAE,DSD_EARNINGS@DF_EARN,1.0` | 2 | 3 | partial local vintage | B | Existing `DF_EARN` vintage is not broad real wage coverage; needs measure filters or better dataflow. |
| 17 | `oecd:OECD.SDD.NAD,DSD_NAMAIN1@DF_TABLE3,1.0` | 2 | 2 | ready fetcher risk | B/C | National accounts finance-sector share. Local TABLE1 exists; TABLE3 not seen locally. |
| 18 | `oecd:OECD.WISE.INE,DSD_IDD@DF_CHILD_POV,1.0` | 2 | 2 | ready shortcut | A/B | Shortcut exists via `DSD_IDD@DF_CHILD_POV`; useful for child-benefit/means-test specs. |
| 19 | `pwt:rconna` | 2 | 2 | ready PWT pseudo-series | A | Fetcher supports `rconna`; no current vintage observed. |
| 20 | OECD PDB variants (`DSD_PDB@DF_PDB_PT`, `DF_PDB_ULC`, `OECD.SDD.NAD.PROD`, `OECD.SDD.STA`) | 2 current, 8 PDB specs | 8+ | alias/canonicalization | A/C | `DSD_PDB@DF_PDB,2.0` is already local and script-supported; variants should canonicalize to the same PDB full vintage plus measure filters. |

Out-of-lane but visible: `oecd:DSD_HEALTH@DF_HEALTH_STAT` has 3 current blockers, but it is primarily welfare/health and should not outrank the productivity/labour pack unless F1 is expanded.

## Fetcher And Alias Status

### OECD Generic SDMX

Status: ready in `publishers.yaml`, module `data.fetchers.oecd`.

Useful existing support:

- full OECD SDMX identifiers pass through to `scripts/fetch.py oecd '<series_id>'`.
- shortcuts already include `DSD_PDB`, `EPL_OV`, `DSD_IDD`, `DSD_TU@DF_TUD`, `TUD`, `DSD_EARN`, `DSD_EARNINGS`, `DSD_PENSIONS@DF_PENSIONS_REPL_RATE`, `DSD_SOCX@DF_SOCX_AGG`, `STAN`, and several National Accounts shortcuts.
- local PDB vintage exists: `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`.
- local labour vintages exist for TUD/CBC/LFS/earnings pieces.

Main problems:

- Several specs cite legacy or short symbolic tokens (`STSIND4_PRODMAN`, `real_average_wage`, `avwage_growth_real`, `industry_concentration`, `value_added_decomposition`, `pension_spending_projections`) that do not directly map to current OECD SDMX dataflow IDs.
- Some source strings use full OECD SDMX IDs with commas. `scripts/derive_coverage.py` currently parses only up to the comma, so coverage output can show misleading series like `OECD.SDD.NAD` or `OECD.ELS.SAE` instead of the full dataflow.
- Some OECD dataflow agencies are stale or inconsistent: `OECD.SDD.STES,DSD_KEI@DF_KEI,4.0` should be tested against current `OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0`; `OECD.ELS.IMM,DSD_DIOC@DF_DIOC,1.0` may need current `OECD.ELS.IMD` migration flows.

### PWT

Status: ready in `publishers.yaml`, module `data.fetchers.pwt`.

Local assets:

- `data/manual/pwt/pwt100.dta`
- `data/vintages/pwt/pwt_full@2026-05-05T195237Z.parquet`
- existing key vintages: `rtfpna`, `hc`, `labsh`, `rgdpe`, `rgdpo`, `rgdpo_per_emp`, `rgdpo_pop`, `avh`, `rkna`, `rgdpna`, `csh_i`.

Manual/API constraint:

- Registry notes manual-drop because GGDC browser download is awkward; the current fetcher tries Dataverse first and falls back to `data/manual/pwt/`. With the manual file already local, the next worker can run PWT pseudo-series commands without external acquisition.

Main alias gaps:

- `pwt:rgdpo_emp` should map to `pwt:rgdpo_per_emp`.
- `pwt:ccon_pop` needs a derived pseudo-series `ccon / pop`.
- `pwt:csh_x` and `pwt:csh_i` are real PWT columns in `pwt_full`; current `_PSEUDO_SERIES` does not list them. `csh_i` has an existing vintage anyway, but fetcher support is inconsistent.
- Source strings like `pwt:rgdpo_pop,rtfpna` should repeat the publisher or be normalized before coverage parsing.

### OECD-STAN

Status: not registered in `publishers.yaml`; no `data.fetchers.oecd_stan` module exists.

Local support:

- generic OECD fetcher has shortcuts: `STAN` and `STAN_VA` -> `OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0`.
- local ad hoc vintage exists: `data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet`.
- offline discovery script reports STAN as mapped and locally present.

Main blocker:

- Hypotheses cite `oecd_stan:*`, but `oecd_stan` is an unresolved publisher in derived coverage. Either add a registry wrapper/alias later or rewrite source tokens to `oecd:STAN` plus derived measure filters.
- Current STAN vintage contains value added, employment, wages, capital stock, and investment measures. It does not directly expose literal TFP; `manufacturing_tfp` and `tfp_growth` require derived productivity proxies or PWT/EU KLEMS fallback.

## Top 20 Fetch/Alias Batch

Commands below are recommendations only. They were not run in this task.

| Batch | Target | Expected data unlocks | Command | Alias/source action after fetch |
| ---: | --- | ---: | --- | --- |
| 1 | OECD EARN-LFS real wage / low-pay panel | 10 current labour runs | `python3 scripts/fetch.py oecd 'DSD_EARN@DF_EARN_LFS' --start 1980 --end 2024` | Map `oecd:DSD_EARN@DF_EARN_LFS` and broad `real_wage_index` requests to the correct `MEASURE` filters. |
| 2 | OECD STAN annual industry pack | 10-11 current STAN-token runs | `python3 scripts/fetch.py oecd 'STAN' --start 2015 --end 2024` | Resolve `oecd_stan:*` by wrapper or alias. Derive manufacturing value added, value added/hour, services productivity; do not claim STAN literal TFP unless a valid measure is confirmed. |
| 3 | PWT labour productivity alias | 4 current runs | `python3 scripts/fetch.py pwt rgdpo_per_emp` | Map `pwt:rgdpo_emp` -> `pwt:rgdpo_per_emp`. Existing vintage may already satisfy this. |
| 4 | PWT net capital stock | 4 current runs | `python3 scripts/fetch.py pwt rnna` | Wire `pwt:rnna` as capital stock/capital-deepening input. |
| 5 | OECD KEI current dataflow | 4 current runs | `python3 scripts/fetch.py oecd 'OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0' --start 1980 --end 2025` | Map stale `OECD.SDD.STES,DSD_KEI@DF_KEI,4.0`, `OutputGap`, and selected short-rate controls to current KEI measures where available. |
| 6 | OECD IDD full panel | 3 current, 8 source refs | `python3 scripts/fetch.py oecd 'DSD_IDD@DF_IDD' --start 1980 --end 2024` | Canonicalize `DSD_IDD@DF_IDD` and `OECD.WISE.INE,DSD_IDD@DF_IDD,1.0` to the WISE IDD vintage. |
| 7 | OECD pension replacement rates | 3 current runs | `python3 scripts/fetch.py oecd 'DSD_PENSIONS@DF_PENSIONS_REPL_RATE' --start 1980 --end 2024` | Map pension replacement-rate specs to this dataflow. |
| 8 | OECD EPL fallback refresh | 3 current, 6 source refs | `python3 scripts/fetch.py oecd 'EPL_OV' --start 1985 --end 2019` | Prefer existing local EPL vintages if present; mark stale blockers as alias-only. |
| 9 | OECD migration high-skill/employment pack | 3 current runs | `python3 scripts/fetch.py oecd 'OECD.ELS.IMM,DSD_DIOC@DF_DIOC,1.0' --start 2000 --end 2024` | If legacy `IMM/DIOC` fails, use current `OECD.ELS.IMD` migration vintages already landed and mark as dataflow-update task. |
| 10 | OECD industrial production legacy token | 3 current runs | `python3 scripts/fetch.py oecd 'STAN' --start 2015 --end 2024` | Map `oecd:STSIND4_PRODMAN` to STAN/NAMAIN manufacturing output only after documenting the estimand shift from short-term industrial production to annual industry output. |
| 11 | OECD LFS indicators | 2 current, 6 source refs | `python3 scripts/fetch.py oecd 'DSD_LFS@DF_LFS_INDIC' --start 1980 --end 2024` | Existing `DSD_LFS_DF_LFS_INDIC@...` vintage likely makes this alias-only. |
| 12 | OECD LFS temporary/non-regular work | 2 current runs | `python3 scripts/fetch.py oecd 'DSD_LFS@DF_LFS_TEMP' --start 1980 --end 2024` | Add loader filters for non-regular/temp worker shares. |
| 13 | OECD union density / coverage alias pack | 2 current, 6+ source refs | `python3 scripts/fetch.py oecd 'DSD_TU@DF_TUD' --start 1980 --end 2024` | Map `DSD_LFS@DF_LFS_UNION`, `DSD_TUD@DF_TUD`, `trade_union_density`, and `union_density` to existing TUD/CBC vintages. |
| 14 | OECD LMS employment status | 2 current runs | `python3 scripts/fetch.py oecd 'OECD.ELS.EMP,DSD_LMS@DF_LMS,1.0' --start 1980 --end 2024` | Wire employment-rate and minijob/share variables. |
| 15 | OECD LMS duration | 2 current, 3 source refs | `python3 scripts/fetch.py oecd 'OECD.ELS.EMP,DSD_LMS@DF_LMS_DURATION,1.0' --start 1980 --end 2024` | Wire long-term unemployment/duration variables. |
| 16 | OECD EARN annual earnings | 2 current, 3 source refs | `python3 scripts/fetch.py oecd 'OECD.ELS.SAE,DSD_EARNINGS@DF_EARN,1.0' --start 1980 --end 2024` | Verify measures; existing `DF_EARN` vintage looked like wage-gap data, not broad real wages. |
| 17 | OECD National Accounts TABLE3 | 2 current runs | `python3 scripts/fetch.py oecd 'OECD.SDD.NAD,DSD_NAMAIN1@DF_TABLE3,1.0' --start 1980 --end 2024` | If TABLE3 fails, use local `DF_TABLE1` or Eurostat sector accounts only with a narrowed estimand. |
| 18 | OECD child poverty | 2 current runs | `python3 scripts/fetch.py oecd 'DSD_IDD@DF_CHILD_POV' --start 1980 --end 2024` | Map child-benefit and means-test poverty specs to child-poverty IDD filters. |
| 19 | PWT real consumption | 2 current runs | `python3 scripts/fetch.py pwt rconna` | Wire real household/quality-adjusted consumption specs; derive per-capita variants from `pop` if needed. |
| 20 | OECD PDB canonical variant pack | 2 current, 8 PDB source specs | `python3 scripts/fetch.py oecd 'DSD_PDB' --start 1970 --end 2025` | Canonicalize `DSD_PDB@DF_PDB_PT`, `DSD_PDB@DF_PDB_ULC`, `OECD.SDD.NAD.PROD,*`, and `OECD.SDD.STA,*` to local PDB plus measure filters. |

Expected yield from the top 20: about 55 current data-blocker unlocks before de-duplication across runs. A realistic graduation yield is lower, roughly 10-20 additional rerunnable candidates, because several high-count items still need design or constructed-variable repair after data wiring.

## Ready-To-Patch Subset

These do not require new data acquisition:

- `pwt:rgdpo_emp` -> `pwt:rgdpo_per_emp`
- `pwt:ccon_pop` -> derive from `pwt:ccon / pwt:pop`
- `pwt:csh_i` / `pwt:csh_x` -> expose PWT full columns as pseudo-series
- `oecd_stan:*` publisher handling -> add wrapper/alias or rewrite to `oecd:STAN` plus derived measure filters
- `oecd:DSD_IDD@DF_IDD` -> existing IDD vintage canonicalization
- `oecd:EPL_OV` and full EPL dataflow -> existing fallback/local vintage canonicalization
- `oecd:TUD`, `DSD_TUD@DF_TUD`, `trade_union_density`, `union_density` -> existing TUD/CBC vintage canonicalization
- OECD PDB variant names -> existing `DSD_PDB@2026-05-12T133454Z.parquet` plus filters

## Needs Fetch But Ready Fetcher

- `DSD_EARN@DF_EARN_LFS`
- `DSD_PENSIONS@DF_PENSIONS_REPL_RATE`
- `DSD_LFS@DF_LFS_TEMP`
- `OECD.ELS.EMP,DSD_LMS@DF_LMS,1.0`
- `OECD.ELS.EMP,DSD_LMS@DF_LMS_DURATION,1.0`
- `DSD_IDD@DF_CHILD_POV`
- `OECD.SDD.NAD,DSD_NAMAIN1@DF_TABLE3,1.0`
- `OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0`

## Needs Catalogue Probe Or Design Decision

- `OECD.ELS.IMM,DSD_DIOC@DF_DIOC,1.0`: likely legacy migration dataflow; current local migration uses `OECD.ELS.IMD`.
- `STSIND4_PRODMAN`: old industrial production token. STAN/NAMAIN annual substitutes change frequency and should be documented.
- `DSD_HEALTH@DF_HEALTH_STAT`: likely wrong shorthand for OECD health data. Out of F1 productivity/labour priority.
- `oecd:industry_concentration`, `oecd:value_added_decomposition`, `oecd:competition_*`, `oecd:venture_capital_*`: OECD symbolic tokens need dataflow discovery, not blind fetches.
- `oecd_stan:manufacturing_tfp`: STAN does not appear to provide literal TFP in the local vintage; derive labour productivity or use PWT/EU KLEMS for TFP.

## Blocker Summary

- Biggest immediate unlock is OECD labour earnings (`DSD_EARN@DF_EARN_LFS`): 10 current run blockers.
- PWT is not the main acquisition blocker. It is mostly local and ready; the next patch should add aliases/derived pseudo-series for `rgdpo_emp`, `ccon_pop`, `csh_i`, and `csh_x`.
- OECD-STAN is the cleanest registry problem: `oecd_stan` is unregistered, but `oecd` already has a STAN shortcut and an ad hoc STAN vintage exists. The next worker should decide whether to add a wrapper publisher or rewrite source tokens to `oecd:STAN`.
- OECD PDB is already powerful locally. The work is canonicalization and measure filters, not another broad fetch.
- Several top data unlocks will not automatically graduate because their runs also have design blockers: absorbed PMR treatment, interaction terms, short samples, or proxy-only estimands.
