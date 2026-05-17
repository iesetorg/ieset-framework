# Graduation Batch A Sample-Ladder Repair - 2026-05-16

Scope: 20 listwise-deletion / sample-collapse candidates from
`engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`.

Read basis:

- `engine/agent_briefs/graduation_repair_swarm_2026-05-16.md`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- candidate `hypotheses/**/*.yaml`
- candidate `engine/runs/*/diagnostics.json`
- `scripts/run_panel_fe.py`
- `scripts/run_did_callaway_santanna.py`

No hypothesis YAML, scripts, run artifacts, scoreboard files, or Reply Guy paths were edited.

## Executive Finding

The main runner already has an implicit sample ladder: `prune_controls_for_overlap(...)`
drops optional controls until the working sample reaches 30 observations. The DiD runner
imports the same helper. Therefore, most Batch A failures are not plain over-control
failures. If a candidate still has `insufficient observations after listwise deletion`,
the collapse is usually in required outcome/treatment/decomposition variables, an
unsupported subnational or micro design, or an arbitrary 30-observation gate applied to a
pre-registered small annual/wave sample.

Near-term `ready_to_patch`: 3 candidates, with estimated real-verdict yield of 2-3 after
patching. Scoreboard-quality yield is lower, probably 1-2, because two ready items are
single-country annual time-series claims.

Do not globally lower the runner's 30-observation gate. The safe route is targeted:

1. Add a time-series/small-wave path for specs that explicitly pre-register a small
   annual or survey-wave sample.
2. Preserve required controls when the falsification rule names them.
3. Treat missing primary variables and wrong-unit designs as data/design blockers, not
   sample-ladder repairs.

## Ready To Patch

| Priority | Candidate | Current collapse | Ladder / robustness path | Minimal patch that preserves claim | Next command |
| ---: | --- | --- | --- | --- | --- |
| 1 | `india_extra_aadhaar_upi_productivity` | `N=27`; no controls. Findex is a four-wave panel, so the generic `min_obs=30` gate is too high for the pre-registered 7-country survey-wave design. | No control ladder needed. The falsification rule is a threshold/differential test, not a control-heavy FE claim. | Add a bespoke threshold/differential runner path for `india_jam_findex_account_ownership_differential_2011_2021`, or extend `scripts/run_descriptive.py` to compute IND 2011-2021 change and peer-mean differential. No YAML claim change needed. | After patch: `python3 scripts/run_panel_fe.py india_extra_aadhaar_upi_productivity --force` if implemented in panel runner, otherwise run the new/bespoke replication wrapper. |
| 2 | `demo_brazil_demographic_transition_inequality` | `N=29` for Gini plus the loaded demographic/minimum-wage channel; PWT labour-productivity overlap is `N=25`, but the falsification rule does not require that control. Current decomposition mode also incorrectly treats the first decomposition channel as the treatment instead of `working_age_population_share`. | No explicit control ladder. The design is explicitly `temporal_structure: time_series`; decomposition channels are part of the claim, not optional controls. | Add a time-series decomposition path in `scripts/run_panel_fe.py` for single-country `panel_fe_decomposition`: use `variables.treatment` as the primary coefficient, keep decomposition channels as channels, use HAC/Newey-West or robust SEs, and allow the pre-registered annual sample below 30. | `python3 scripts/run_panel_fe.py demo_brazil_demographic_transition_inequality --force` |
| 3 | `demo_mexico_fertility_decline_wages` | Core wage plus working-age-share plus net migration gives `N=22`; adding labour productivity gives `N=18`. The generic 30-observation gate is the immediate blocker. | No robustness-only control path: the rule says the effect should survive productivity and net migration. YAML notes explicitly call for Mexico-only time-series with Newey-West HAC. | Add the same single-country time-series path. Keep the primary model with net migration and report the productivity-control model even at lower N; do not silently drop productivity from the dispositive interpretation. Borderline because `N=18` is thin. | `python3 scripts/run_panel_fe.py demo_mexico_fertility_decline_wages --force` |

Expected graduation yield from these three: `india_extra_aadhaar_upi_productivity` is high
probability to become a real verdict because the rule is a direct threshold test over loaded
Findex data. The two demographic time-series cases are medium / medium-low: they should
graduate to real verdicts if the coefficients can be estimated, but may remain weak or
partial because the usable samples are thin.

## Candidate Diagnostics

| Candidate | Collapse diagnosis | Control ladder or robustness-only path? | Patch status |
| --- | --- | --- | --- |
| `competition_enforcement_consumer_welfare_effect` | Required outcome is sparse: `industry_markup_index` from OECD PMR has only 2 waves per country, `N=22`. GDP and trade controls do not reduce the sample. Missing registered outcomes: `hhi_concentration_index`, `consumer_price_to_marginal_cost_ratio`. | No control ladder. This is a missing/weak outcome problem. | `needs_data`: sector concentration / markup / consumer-welfare panel. A min-N patch would only graduate a two-wave PMR proxy, not the claim. |
| `post_covid_inflation_episode_supply_vs_demand_decomposition` | `N=0` after loaded global/US channels are treated as country-year regressors. Missing `shadow_fed_funds_rate`, `ecb_policy_rate`, and `covid_labour_supply_shock`. Oil/gas global channels are not expanded across the 7-country sample. | No control ladder. The rule is a Bernanke-Blanchard-style structural decomposition. | `needs_design_decision` plus `needs_data`: build a bespoke quarterly decomposition; do not repair via FE control dropping. |
| `interest_rate_hike_distributional_upward_redistribution` | `N=0`: loaded distributional outcome countries do not overlap with loaded policy-rate treatment countries. Missing primary quintile disposable-income growth, mortgage-payment ratio, and quintile CPI. | No control ladder. | `needs_data`: distributional household/quintile data and mortgage/renter incidence; likely bespoke majority-gate runner. |
| `austrian_monetary_expansion_asset_bubble_not_cpi_panel` | `N=21`; broad money and base money load only for USA over 1987-2007 while outcomes/controls cover the 12-country sample. Controls do not collapse the sample. | Robustness note only: post-2008 sub-sample. No control-ladder path for the primary. | `needs_data_or_source_mapping`: multi-country broad/base money union or WDI/IMF money proxy. Do not graduate as USA-only. |
| `demo_brazil_demographic_transition_inequality` | `N=29`; labour productivity drops to `N=25`, but the main blocker is generic min-N and decomposition runner treatment selection. | Time-series design is pre-registered; no optional control ladder. | `ready_to_patch`. |
| `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020` | `N=13`; key CPI, expectations, M2, and balance-sheet treatment load for USA only. Output-gap, unemployment, and oil controls are not the blocker. Missing constructed `core_cpi_divergence_from_pre2008_trend`. | Robustness exists for alternative CPI / balance-sheet metrics, but output-gap and oil controls are in the primary rule. | `needs_data`: non-US central-bank balance-sheet, core CPI/expectations, and constructed trend-divergence channel. |
| `high_income_escape_market_openness_1950_2024` | Interaction construction yields only `N=8` because `domestic_market_competition` from OECD PMR is very sparse. Missing `tariff_protection_avg` and `human_capital`. | No control ladder. The interaction is the estimand. | `needs_data`: tariff/protection and long-run competition measure; PMR-only interaction is too narrow. |
| `child_benefit_expansion_child_poverty_effect` | `N=2`; WDI national poverty proxy barely overlaps USA/GBR event sample. Missing OECD child-poverty outcome. Controls do not drive the collapse. | Pandemic exclusion is registered as robustness, not a control ladder. | `needs_data`: OECD IDD child poverty, US Census SPM, UK HBAI, or a bespoke two-country event runner once data land. |
| `chips_act_2022_semiconductor_capacity_2024_2027` | `N=9`; loaded construction proxy is US-heavy and early-window only. Missing advanced-node capacity, US share of global logic capacity, obligated outlays, global demand, and export-control intensity. Also the registered 2027 outcome is not yet observable on 2026-05-16. | Secondary synthetic-control robustness is registered; export controls are a required confounder, not optional. | `needs_data` plus `needs_design_decision`: hold final capacity claim until 2027 data or narrow to an explicitly interim construction-start verdict. |
| `india_extra_aadhaar_upi_productivity` | `N=27`; no controls; all primary Findex variables load. Collapse is the generic min-N gate against a 4-wave survey panel. | No control ladder needed. | `ready_to_patch`. |
| `global_value_chain_participation_upgrade` | `N=23` only because the runner falls through to `domestic_entry_freedom_index` as the treatment. The registered GVC treatment and TiVA channels are missing. Controls do not collapse the sample. | Bartik-IV is registered as robustness after the primary interaction, but the primary `GVC x entry_freedom` estimand is not loadable. | `needs_data`: OECD TiVA GVC participation/backward/forward linkages and manufacturing wage outcome. |
| `monopoly_capital_concentration_markup_link` | `N=24` on aggregate US proxy; adding capital stock gives `N=23`. The deeper issue is wrong unit: claim asks for industry-FE concentration -> markup with productivity-dispersion control, but loaded proxy is aggregate manufacturing share. | No safe ladder. Productivity-dispersion control is discriminating in the rule. | `needs_data_or_design`: industry concentration/markup/productivity dispersion panel. Do not graduate via aggregate WDI manufacturing share. |
| `demo_mexico_fertility_decline_wages` | `N=22` base, `N=18` with productivity. Generic min-N blocks a pre-registered single-country HAC time-series design. | No robustness-only path for productivity; it is named in the falsification rule. | `ready_to_patch`, borderline. |
| `welfare_transfer_indonesia_pkh_blt_2007_2022` | `N=20` country-year rows. YAML asks for province FE / PKH-BLT channels, but current variables are WDI country-year proxies. Missing child-underweight channel. | No control ladder. | `needs_data`: province/household PKH, BLT, poverty, school, consumption, and nutrition panels. Generic DiD cannot identify this from country-year WDI. |
| `welfare_transfer_china_dibao_rural_pension_2009` | `N=12` country-year rows. YAML asks for province FE, but current treatment/outcome proxies are WDI country-year. | No control ladder. | `needs_data`: province/rural NRPS/Dibao rollout, spending, poverty, and migration panel. |
| `welfare_transfer_kenya_hsnp_2015_consumption_smoothing` | `N=13`; country-year WDI consumption/rainfall proxy cannot support county/household shock-trigger DiD. Missing severe-food-insecurity outcome. | No control ladder. | `needs_data`: HSNP recipient/trigger, household or county consumption, drought, and food-insecurity data. |
| `zimbabwe_land_reform_cause_decomposition` | `N=0` once terms-of-trade/global controls and land/sanctions channels are combined. Missing fast-track event treatment, fiscal-military channel, monetary-financing channel, and drought indicator. | No control ladder. This is a variance-decomposition/checklist claim. | `needs_design_decision` plus `needs_data`: use bespoke annual decomposition/checklist; do not force panel FE. |
| `tax_inequality_brazil_tax_base_evolution` | `N=28` for disposable Gini plus government-consumption transfer proxy, but `top_marginal_income_tax_rate` has zero Brazil overlap in the sample. Dropping it removes the tax-side discriminator. | Robustness mentions Lustig-CEQ-style fiscal incidence; not a control ladder. | `needs_data`: Brazil tax-progressivity/top-rate and fiscal-incidence decomposition, ideally pretax vs disposable Gini. |
| `uk_real_wage_stagnation_2008_present_decomposition` | `N=21`; migration and EPL channels further reduce overlap. Missing `gdp_per_hour_worked`. Loaded `median_real_wage_index` maps to an OWID trust-attitudes source, so the primary outcome mapping is suspect. | No control ladder. | `needs_data_or_mapping`: UK real median wage / ASHE or OECD earnings plus OECD PDB GDP-hour productivity and channel mapping. |
| `welfare_transfer_finland_basic_income_experiment_2017` | `N=6`; current variables are national OECD LFS rows, not the individual-level RCT. Missing self-reported wellbeing. | No control ladder. | `needs_data_or_design`: Kela experiment employment/wellbeing micro or published treatment-control summary; bespoke RCT result parser. |

## Needs Data

Highest leverage data/source packs from this batch:

1. OECD / OECD PMR / OECD STAN / OECD PDB / OECD IDD:
   `competition_enforcement_consumer_welfare_effect`,
   `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`,
   `child_benefit_expansion_child_poverty_effect`,
   `uk_real_wage_stagnation_2008_present_decomposition`.
   Starter commands after confirming keys:
   - `python3 scripts/fetch.py oecd 'OECD.WISE.INE,DSD_IDD@DF_CHILD_POV,1.0' --start 2000 --end 2024`
   - `python3 scripts/fetch.py oecd 'OECD.SDD.NAD.PROD,DSD_PDB@DF_PDB_GR,1.0' --start 1995 --end 2024`
   - `python3 scripts/fetch.py oecd STAN --start 1980 --end 2024`
2. TiVA / GVC:
   `global_value_chain_participation_upgrade`.
   No confirmed local `oecd_tiva` fetch path was found in this pass; needs a source-pack worker before rerun.
3. Subnational / micro welfare-transfer data:
   `welfare_transfer_indonesia_pkh_blt_2007_2022`,
   `welfare_transfer_china_dibao_rural_pension_2009`,
   `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`,
   `welfare_transfer_finland_basic_income_experiment_2017`.
   These need manual/derived panels; WDI country-year proxies are not enough.
4. Monetary/source-union pack:
   `austrian_monetary_expansion_asset_bubble_not_cpi_panel`,
   `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`,
   `post_covid_inflation_episode_supply_vs_demand_decomposition`,
   `interest_rate_hike_distributional_upward_redistribution`.
   Required work is mostly multi-country central-bank source mapping, not control pruning.
5. Manual/fiscal/industry packs:
   `chips_act_2022_semiconductor_capacity_2024_2027`,
   `monopoly_capital_concentration_markup_link`,
   `tax_inequality_brazil_tax_base_evolution`,
   `zimbabwe_land_reform_cause_decomposition`.

## Needs Design Decision

These should not be patched by a generic sample ladder:

- `post_covid_inflation_episode_supply_vs_demand_decomposition`: structural quarterly decomposition, not panel FE.
- `interest_rate_hike_distributional_upward_redistribution`: multi-outcome majority gate over distributional incidence; needs bespoke household/incidence runner.
- `chips_act_2022_semiconductor_capacity_2024_2027`: registered end window extends to 2027; either hold final verdict or explicitly narrow to interim construction-start evidence.
- `welfare_transfer_indonesia_pkh_blt_2007_2022`, `welfare_transfer_china_dibao_rural_pension_2009`, `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`: declared province/county/household designs cannot be identified from country-year WDI panels.
- `zimbabwe_land_reform_cause_decomposition`: variance-decomposition/checklist claim; generic FE is the wrong estimator.
- `tax_inequality_brazil_tax_base_evolution`: descriptive fiscal-incidence decomposition, not a disposable-Gini-on-government-consumption FE claim.
- `uk_real_wage_stagnation_2008_present_decomposition`: residual-share decomposition; first repair the wage/productivity mappings.
- `welfare_transfer_finland_basic_income_experiment_2017`: RCT/published-summary parser, not national panel FE.

## Exact Patch Targets

Ready-to-patch implementation files:

- `scripts/run_panel_fe.py`
  - Add a targeted time-series path for `sample.temporal_structure: time_series` or single-country specs whose estimator notes explicitly call for HAC/Newey-West.
  - For `panel_fe_decomposition`, prefer `variables.treatment` as the primary coefficient when present; treat `decomposition_channels` as channels/extra regressors instead of replacing the treatment.
  - Do not globally lower `min_obs=30`; make the exception explicit and record it in diagnostics.
- `scripts/run_descriptive.py` or a new bespoke run wrapper
  - Implement `india_jam_findex_account_ownership_differential_2011_2021`: IND 2021 minus 2011, peer mean change, and threshold comparison from the falsification rule.

Post-patch focused commands:

```bash
python3 scripts/run_panel_fe.py india_extra_aadhaar_upi_productivity --force
python3 scripts/run_panel_fe.py demo_brazil_demographic_transition_inequality --force
python3 scripts/run_panel_fe.py demo_mexico_fertility_decline_wages --force
```

Then inspect:

```bash
jq '.verdict, .estimate, .data_status.variables_missing' engine/runs/india_extra_aadhaar_upi_productivity/diagnostics.json
jq '.verdict, .estimate, .data_status.variables_missing' engine/runs/demo_brazil_demographic_transition_inequality/diagnostics.json
jq '.verdict, .estimate, .data_status.variables_missing' engine/runs/demo_mexico_fertility_decline_wages/diagnostics.json
```

For all other candidates, run only after the listed data/design blocker is repaired:

```bash
python3 scripts/run_panel_fe.py <panel_fe_candidate_id> --force
python3 scripts/run_did_callaway_santanna.py <did_candidate_id> --force
```

## Prioritized Subsets

`ready_to_patch`:

1. `india_extra_aadhaar_upi_productivity`
2. `demo_brazil_demographic_transition_inequality`
3. `demo_mexico_fertility_decline_wages`

`needs_data`:

- `competition_enforcement_consumer_welfare_effect`
- `post_covid_inflation_episode_supply_vs_demand_decomposition`
- `interest_rate_hike_distributional_upward_redistribution`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`
- `high_income_escape_market_openness_1950_2024`
- `child_benefit_expansion_child_poverty_effect`
- `chips_act_2022_semiconductor_capacity_2024_2027`
- `global_value_chain_participation_upgrade`
- `monopoly_capital_concentration_markup_link`
- `welfare_transfer_indonesia_pkh_blt_2007_2022`
- `welfare_transfer_china_dibao_rural_pension_2009`
- `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`
- `zimbabwe_land_reform_cause_decomposition`
- `tax_inequality_brazil_tax_base_evolution`
- `uk_real_wage_stagnation_2008_present_decomposition`
- `welfare_transfer_finland_basic_income_experiment_2017`

`needs_design_decision`:

- `post_covid_inflation_episode_supply_vs_demand_decomposition`
- `interest_rate_hike_distributional_upward_redistribution`
- `chips_act_2022_semiconductor_capacity_2024_2027`
- `welfare_transfer_indonesia_pkh_blt_2007_2022`
- `welfare_transfer_china_dibao_rural_pension_2009`
- `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`
- `zimbabwe_land_reform_cause_decomposition`
- `tax_inequality_brazil_tax_base_evolution`
- `uk_real_wage_stagnation_2008_present_decomposition`
- `welfare_transfer_finland_basic_income_experiment_2017`
