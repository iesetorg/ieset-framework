# Graduation Repair Swarm Synthesis - 2026-05-16

Purpose: consolidate the six-agent repair/data swarm into a single execution
plan for graduating additional hypotheses from the current inconclusive pool.

Inputs:

- `engine/agent_briefs/graduation_repair_swarm_2026-05-16.md`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- `engine/audits/graduation_batch_A_sample_ladder_repair_2026-05-16.md`
- `engine/audits/graduation_batch_B_absorbed_treatment_repair_2026-05-16.md`
- `engine/audits/graduation_batch_C_interaction_constructs_2026-05-16.md`
- `engine/audits/graduation_batch_D_variable_mapping_2026-05-16.md`
- `engine/audits/graduation_data_pack_oecd_pwt_2026-05-16.md`
- `engine/audits/graduation_data_pack_macro_trade_labour_2026-05-16.md`

No hypothesis YAML, runner code, data vintages, scoreboards, or run artifacts
were edited by this synthesis.

## Bottom Line

The initial target of graduating 10-20 additional hypotheses is still realistic,
but not from a blind rerun. The clean immediate repair pool is about 10-13
candidates:

- 10 candidates are patch-ready with low or moderate implementation risk.
- 3 more are plausible if event/stub metadata repairs from Batch E are treated as
  a separate mini-lane.
- The expected first-pass graduation yield after repair is 8-12 real verdicts.
- Reaching the upper 10-20 target likely requires the alias/data batch,
  especially OECD/PWT/OECD-STAN and selected FRED/BLS/ECB/Eurostat/IMF pulls.

The key lesson: most remaining inconclusives are not "just rerun it" failures.
They are fixed-effect absorption, wrong-unit designs, missing interaction
components, source-token drift, or real data gaps.

## Lane Results

| Lane | Scope | Patch-ready | Expected yield | Main finding |
| --- | ---: | ---: | ---: | --- |
| A - sample ladder | 20 | 3 | 2-3 real verdicts | Generic `min_obs=30` is blocking pre-registered small annual/wave designs; most other cases are true data/design gaps. |
| B - absorbed treatment | 10 | 3 + 1 research-grade | 3 real verdicts | Three specs need reduced FE or corrected treatment construction, not more data. |
| C - interactions | 6 | 1 | 0-1 real verdict | Only `welfare_state_market_flexibility_complement` has local inputs for both interaction components. |
| D - variable mapping | 19 | 3 + 1 optional design proxy | 2-3 real verdicts | Three are source/runner mapping repairs; most others require BIT, tariffs, SOE, antitrust, WIPO, licensing, sector, or subnational data. |
| F1 - OECD/PWT/STAN data | large | alias/fetch pack | 10-20 rerunnable candidates after data work | Biggest source unlock is OECD earnings; PWT is mostly alias/derived pseudo-series; STAN needs wrapper/alias support. |
| F2 - macro/trade/labour data | large | alias/fetch pack | high after keys/manual drops | FRED requires `FRED_API_KEY`; BLS key is strongly recommended; BOJ and IMF IFS need manual drops; Comtrade/WITS product data need fetcher/key work. |

## First Implementation Batch

Patch these first because they either preserve the written falsification test or
only repair source/schema drift. They should be run immediately after patching.

| Priority | Candidate | Repair | File area | Expected result |
| ---: | --- | --- | --- | --- |
| 1 | `universal_healthcare_cost_outcome_oecd` | Use year FE only; country FE absorb the universal-system indicator. | hypothesis YAML | Real verdict likely. |
| 2 | `asia_pakistan_imf_programme_cycle_1988_2024` | Use year FE only; Pakistan-vs-peer contrast is country-constant. | hypothesis YAML | Real verdict likely. |
| 3 | `export_openness_agricultural_diversification` | Use persistent post indicators for CHL/NZL/VNM and move WGI rule-of-law out of the primary sample. | hypothesis YAML / constructed parsing if needed | Real verdict likely, probably partial. |
| 4 | `startup_density_frontier_prosperity` | Add WDI new-business-density fallback for `startup_density`. | hypothesis YAML | Real verdict possible if overlap survives. |
| 5 | `minimum_wage_youth_unemployment_tradeoff` | Bridge the statutory-minimum-wage constructed phrase to local derived minimum-wage-bite vintage. | `scripts/run_panel_fe.py` | Real verdict likely if overlap survives. |
| 6 | `fiat_expansion_erodes_currency_purchasing_power_long_run` | Convert to descriptive and bridge commodity basket to `imf_pcps:PALLFNF`. | hypothesis YAML / source bridge | Descriptive real verdict likely; inspect semantics before scoreboard promotion. |

Recommended commands after patch:

```bash
python3 scripts/run_panel_fe.py universal_healthcare_cost_outcome_oecd --force
python3 scripts/run_panel_fe.py asia_pakistan_imf_programme_cycle_1988_2024 --force
python3 scripts/run_panel_fe.py export_openness_agricultural_diversification --force
python3 scripts/run_panel_fe.py startup_density_frontier_prosperity --force
python3 scripts/run_panel_fe.py minimum_wage_youth_unemployment_tradeoff --force
python3 scripts/run_descriptive.py fiat_expansion_erodes_currency_purchasing_power_long_run --force
```

## Second Implementation Batch

Patch these after the first batch because they touch runner behavior or produce
thinner evidence. They are still worth doing, but should be audited closely.

| Priority | Candidate | Repair | File area | Risk |
| ---: | --- | --- | --- | --- |
| 1 | `india_extra_aadhaar_upi_productivity` | Add a bespoke Findex threshold/differential path for the four-wave sample. | `scripts/run_descriptive.py` or dedicated wrapper | Low. The current `N=27` is a generic gate problem. |
| 2 | `demo_brazil_demographic_transition_inequality` | Add single-country time-series/decomposition path and use `variables.treatment` as the primary coefficient. | `scripts/run_panel_fe.py` | Medium. Thin sample, but registered as time series. |
| 3 | `demo_mexico_fertility_decline_wages` | Same time-series/HAC path; report productivity-control model even with lower N. | `scripts/run_panel_fe.py` | Medium-high. `N=18` with productivity is thin. |
| 4 | `welfare_state_market_flexibility_complement` | Add SOCX welfare-state slice and construct flexibility-openness-discipline index from PMR/EPL/trade/debt. | `scripts/run_panel_fe.py` plus YAML source token | Medium. Interaction support is present once components load. |
| 5 | `demo_life_expectancy_lfp_panel` | Correct WHO GHO source to `who_gho:WHOSIS_000015`. | hypothesis YAML | Research-grade only until pension-age control is present. |

Recommended commands after patch:

```bash
python3 scripts/run_panel_fe.py india_extra_aadhaar_upi_productivity --force
python3 scripts/run_panel_fe.py demo_brazil_demographic_transition_inequality --force
python3 scripts/run_panel_fe.py demo_mexico_fertility_decline_wages --force
python3 scripts/run_panel_fe.py welfare_state_market_flexibility_complement --force
python3 scripts/run_panel_fe.py demo_life_expectancy_lfp_panel --force
```

## Batch E Mini-Lane

Batch E was not separately audited by this swarm, but the broad plan marked it
as a likely high-yield event/stub metadata lane:

- `abenomics_monetary_fiscal_coordination_effect`
- `china_1978_price_liberalisation_growth_decomposition`
- `soviet_collectivisation_agricultural_marketings`

Next worker task: inspect these three specs and current diagnostics, then patch
only if event years and falsification thresholds are obvious and defensible.

## Data And Alias Batch

This is the path to push beyond the first 8-12 likely graduations.

### Alias-first, no new external data

- `pwt:rgdpo_emp` -> `pwt:rgdpo_per_emp`
- `pwt:ccon_pop` -> derive from `pwt:ccon / pwt:pop`
- `pwt:csh_i` and `pwt:csh_x` -> expose PWT full columns as pseudo-series
- `oecd_stan:*` -> wrapper/alias to `oecd:STAN` plus measure filters
- OECD IDD, EPL, TUD/CBC, and PDB variants -> canonicalize to existing local
  vintages
- `ilostat:unemployment_rate` -> existing `UNE_2EAP_SEX_AGE_RT_A` bridge
- `imf_pcps:POILBRE` and `imf_pcps:Primary` -> existing/materialized PCPS
  series
- `imf:WEO.NGDP_RPCH` -> `imf:NGDP_RPCH`
- ECB `MRR_FR` and `IRS.M.DE` shortcuts -> canonical storage aliases
- WITS/Comtrade concentration tokens -> `wits:export_product_hhi_wits` only
  when the estimand is benchmark export concentration

### Ready fetches, credential/manual constraints noted

OECD/PWT/STAN:

```bash
python3 scripts/fetch.py oecd 'DSD_EARN@DF_EARN_LFS' --start 1980 --end 2024
python3 scripts/fetch.py oecd 'STAN' --start 2015 --end 2024
python3 scripts/fetch.py pwt rgdpo_per_emp
python3 scripts/fetch.py pwt rnna
python3 scripts/fetch.py oecd 'OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0' --start 1980 --end 2025
python3 scripts/fetch.py oecd 'DSD_IDD@DF_IDD' --start 1980 --end 2024
python3 scripts/fetch.py oecd 'DSD_PENSIONS@DF_PENSIONS_REPL_RATE' --start 1980 --end 2024
python3 scripts/fetch.py oecd 'EPL_OV' --start 1985 --end 2019
python3 scripts/fetch.py oecd 'DSD_IDD@DF_CHILD_POV' --start 1980 --end 2024
python3 scripts/fetch.py oecd 'DSD_PDB' --start 1970 --end 2025
```

Macro/labour:

```bash
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred WUXIASHADOWRATE
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred M1204AUSM363SNBR
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred IRLTLT30JPM156N
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred FRBATLWGT12MMUMHWGO
BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls CES1021100001
BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls OEUM000000000000000001
python3 scripts/fetch.py eurostat sts_inppd_q
python3 scripts/fetch.py ecb IRS.M.DE
python3 scripts/fetch.py imf GGX_NGDP
python3 scripts/fetch.py imf GGSB_NPGDP
```

Manual-drop lanes:

- BOJ: stage one CSV/XLS/XLSX at a time under `data/manual/boj/`, then run
  `python3 scripts/fetch.py boj <series_id>`.
- IMF IFS/BOP/AREAER: export files to `data/manual/imf_ifs/`, then run
  `python3 scripts/fetch.py imf_ifs <series_id>`.
- UN Comtrade / WITS product-line / BACI HS6: still needs key/fetcher/source
  spine work. WITS HHI is useful, but it does not solve tariffs, import/export
  values, HS6 counts, RCA, Theil, top-product shares, or CBAM product-family
  flows.

## Do Not Patch Blindly

Hold these until data or design is repaired:

- Subnational/micro designs currently represented by country-year proxies:
  Indonesia PKH/BLT, China Dibao/NRPS, Kenya HSNP, Finland basic income,
  Stockton SEED, free community college.
- Product/HS-code designs without HS-unit support:
  Trump tariff manufacturing reshoring, Comtrade product lines, CBAM flows.
- Sector/firm concentration or industrial-policy claims without real
  concentration/state-aid/SOE/zombie-firm data.
- Claims whose current proxy would change the estimand materially:
  Malaysia post-1990 proxy, China SOE vs CEE privatisation, Bangladesh apparel,
  Australia Hawke-Keating, OECD PMR TFP with only late PMR waves.

## Recommended Next Worker Split

1. Low-risk YAML/schema patch worker:
   `universal_healthcare_cost_outcome_oecd`,
   `asia_pakistan_imf_programme_cycle_1988_2024`,
   `export_openness_agricultural_diversification`,
   `startup_density_frontier_prosperity`,
   `fiat_expansion_erodes_currency_purchasing_power_long_run`.

2. Runner support worker:
   minimum-wage derived bridge, Findex descriptive path, single-country
   time-series/HAC path, SOCX/flexibility interaction construction.

3. Alias/data worker:
   PWT pseudo-series, OECD-STAN wrapper/alias, OECD IDD/EPL/TUD/PDB
   canonicalization, ILO/IMF/ECB stale aliases, and fetcher-ready OECD/FRED/BLS
   queue once keys are available.

4. Event metadata worker:
   inspect Batch E and patch only if the event years and falsification rules are
   already defensible from the spec and current data.

This split should let the next pass produce meaningful graduations while also
building the data runway for the larger 394-spec backlog.
