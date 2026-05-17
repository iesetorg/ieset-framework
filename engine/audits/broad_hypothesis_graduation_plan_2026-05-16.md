# Broad Hypothesis Graduation Plan - 2026-05-16

Purpose: step back from the first 66-run pass and identify the next batchable graduation lanes across the whole local hypothesis/run corpus.

## Current Corpus State

Structured scan:

| Item | Count |
| --- | ---: |
| Hypothesis YAML files on disk | 1,629 |
| Existing run diagnostics | 1,607 |
| Standard runnable-candidate YAMLs scanned | 1,628 |
| Source-ready supported-template specs | 1,210 |
| Specs still needing data | 394 |
| Specs needing/unsupported template work | 24 |

Current run verdict families after the 66-run wave:

| Verdict family | Count |
| --- | ---: |
| `partial` | 790 |
| `supported` | 454 |
| `refuted` | 164 |
| `inconclusive` | 190 |
| `unknown` | 8 |
| `blocked` | 1 |

Scoreable real-verdict family today: `1,408` (`supported + partial + refuted`).

## Lesson From The 66-Run Wave

The preflight-ready queue was too permissive. It correctly found cases where the runner could load some variables, but many still failed estimator-specific gates after filtering.

Result from the 66 attempted queue:

| Result | Count |
| --- | ---: |
| Graduated to real verdict | 3 |
| Stayed inconclusive | 63 |
| Crashed | 0 |

Graduated:

- `nuclear_phaseout_accident_risk_reduction_value` -> `SUPPORTED`
- `labour_market_reform_almp_complementarity_effect` -> `SUPPORTED`
- `wto_accession_productivity_spillover_panel` -> `PARTIAL`

Therefore the next graduation batches should not be blind reruns. They should repair design, sample, variable construction, or missing data first.

## Current Inconclusive Pool

Current inconclusive runs: `190`.

| Blocker family | Count | Graduation route |
| --- | ---: | --- |
| Data/schema: no outcome or decomposition channel loaded | 59 | Fetch or map source tokens; add derived outcome builders where data exists. |
| Unspecified pending data | 21 | Inspect run card/spec and convert to concrete missing-source tasks. |
| Listwise-deletion/sample collapse | 20 | Add sample ladders, drop overrestrictive controls, or make controls robustness-only. |
| Treatment/variable mapping missing | 19 | Build treatment proxies/constructed variables or rewrite source mapping. |
| Synth-DiD pre-period/donor shortage | 17 | Expand donor pools, relax sample, or convert to event/descriptive design. |
| Event-window pre/post shortage | 12 | Fix event years/windows only if preregistered design permits; otherwise hold. |
| No within-country treatment variation | 10 | Switch design or fixed effects; do not force TWFE with absorbed treatments. |
| Manual/data-drop gaps | 7 | Manual-source acquisition or bespoke fetchers. |
| Interaction construct needed | 6 | Build explicit interaction variables and rerun. |
| Coverage gate insufficient | 5 | Coverage expansion or keep inconclusive. |
| Too few observations for LP | 3 | Convert to event/descriptive or expand panel; LP is unsuitable as-is. |
| Event year missing | 2 | Add event-year metadata and rerun. |
| State/subnational panel data needed | 2 | BLS/state panel acquisition. |
| Country not in panel | 1 | Country-code/sample mapping repair. |
| Stub falsification rule | 1 | Sharpen rule before grading. |
| Donor pool too small | 1 | Add donors or change design. |
| Other | 3 | Manual review. |

## Highest-Yield Graduation Batches

### Batch A - Sample-Ladder Repair

Size: `20`.

Targets: listwise-deletion/sample-collapse cases.

Why first: the data usually exist; the model is losing the sample after controls. These can often graduate by reporting a control ladder rather than imposing all controls in the primary model.

Candidate IDs:

- `competition_enforcement_consumer_welfare_effect`
- `post_covid_inflation_episode_supply_vs_demand_decomposition`
- `interest_rate_hike_distributional_upward_redistribution`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `demo_brazil_demographic_transition_inequality`
- `central_bank_balance_sheet_cpi_decoupling_panel_2008_2020`
- `high_income_escape_market_openness_1950_2024`
- `child_benefit_expansion_child_poverty_effect`
- `chips_act_2022_semiconductor_capacity_2024_2027`
- `india_extra_aadhaar_upi_productivity`
- `global_value_chain_participation_upgrade`
- `monopoly_capital_concentration_markup_link`
- `demo_mexico_fertility_decline_wages`
- `welfare_transfer_indonesia_pkh_blt_2007_2022`
- `welfare_transfer_china_dibao_rural_pension_2009`
- `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`
- `zimbabwe_land_reform_cause_decomposition`
- `tax_inequality_brazil_tax_base_evolution`
- `uk_real_wage_stagnation_2008_present_decomposition`
- `welfare_transfer_finland_basic_income_experiment_2017`

Expected yield: medium. These are not guaranteed, but this is the cleanest design-repair lane.

### Batch B - Absorbed Treatment / Wrong FE Design

Size: `10`.

Targets: no within-country treatment variation under country fixed effects.

Why second: these are conceptually clear failures. The current estimator is asking TWFE to identify country-constant or single-country indicators. They need event-study, synthetic-control, cross-sectional, or reduced-FE designs.

Candidate IDs:

- `oecd_product_market_deregulation_tfp_panel`
- `universal_healthcare_cost_outcome_oecd`
- `asia_bangladesh_apparel_growth_1985_2024`
- `china_soe_vs_cee_privatised_growth`
- `demo_canada_points_system_immigration`
- `export_openness_agricultural_diversification`
- `demo_life_expectancy_lfp_panel`
- `asia_pakistan_imf_programme_cycle_1988_2024`
- `australia_hawke_keating_reform_long_run`
- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`

Expected yield: medium-high after design repair; low if simply rerun.

### Batch C - Constructed Interactions

Size: `6`.

Targets: specs that explicitly require an interaction term, but the generic runner has no loadable constructed interaction.

Candidate IDs:

- `incumbent_subsidy_market_share_persistence`
- `policy_uncertainty_private_investment`
- `welfare_state_market_flexibility_complement`
- `east_asia_export_discipline_vs_domestic_protection`
- `universal_vs_meanstest_child_poverty`
- `industrial_policy_corruption_interaction`

Expected yield: high if the component variables already load; otherwise falls into data-fetch lane.

### Batch D - Treatment / Variable Mapping

Size: `19`.

Targets: no treatment variable loaded, no outcome/treatment in spec, or required variables not mapped.

Why: this is mostly schema and constructed-variable work. Some will be easy proxy wiring; others need real data.

Examples:

- `state_credit_allocation_zombie_firm_persistence`
- `trump_tariff_manufacturing_reshoring_effect`
- `malaysia_developmentalist_plateau_1990_2024`
- `tariff_protection_duration_growth_drag`
- `minimum_wage_youth_unemployment_tradeoff`
- `startup_density_frontier_prosperity`
- `free_community_college_enrolment_completion`
- `state_owned_enterprise_share_growth_plateau`
- `occupational_licensing_productivity_drag`
- `industrial_concentration_labour_share_link`
- `bilateral_investment_treaty_fdi_panel`
- `colonial_institutions_post_independence_growth`
- `industrial_policy_without_exit_discipline_failure`
- `demo_migration_inflows_wages_skill_split`
- `national_champions_long_run_productivity_drag`
- `competition_policy_enforcement_innovation`

Expected yield: mixed. Best handled by small focused workers, not a single runner batch.

### Batch E - Event Metadata And Stub Rules

Size: `3`.

Candidate IDs:

- `abenomics_monetary_fiscal_coordination_effect`
- `china_1978_price_liberalisation_growth_decomposition`
- `soviet_collectivisation_agricultural_marketings`

Expected yield: high if event years and falsification thresholds are obvious and defensible.

### Batch F - Data Fetch / Source Mapping

Size: large; `394` specs still need data in the broad source-readiness audit.

Top missing source families by unresolved token references:

| Publisher/source family | Missing-token references |
| --- | ---: |
| OECD | 196 |
| IMF | 74 |
| World Bank WDI | 59 |
| FRED | 49 |
| OWID | 46 |
| BOJ | 39 |
| BLS | 37 |
| ECB | 35 |
| ILOSTAT | 28 |
| Eurostat | 21 |
| INDEC | 20 |
| PWT | 17 |
| ONS | 13 |
| OECD STAN | 13 |
| WHO GHO | 12 |
| UN Comtrade | 11 |
| WITS | 9 |
| UNCTAD | 8 |

Best data-fetch batches:

1. OECD/PWT/OECD-STAN productivity and labour pack.
2. BLS/state panel pack for minimum-wage and US labour cases.
3. Trade product pack: WITS HHI already added; next BACI/Comtrade product lines.
4. Macro/monetary pack: FRED, BOJ, ECB, IMF/REER.
5. Manual country packs: INDEC Argentina, Singapore HDB, Cuba special-period, country case studies.

Expected yield: high over multiple runs, but only after fetchers/source mappings are repaired.

### Batch G - Hard Redesign / Low Immediate Yield

These are real hypotheses, but not good blind graduation targets:

- Synth-DiD pre-period/donor shortage: `17`
- Event-window pre/post shortage: `12`
- Local-projection too few observations: `3`
- Coverage gate insufficient: `5`

These need design decisions, wider donor/sample definitions, or a decision to keep them inconclusive.

## Recommended Execution Order

1. Freeze the three new real verdicts and review their result cards.
2. Run Batch A as a sample-ladder repair wave, not a direct rerun.
3. Run Batch B as a design-conversion wave.
4. Run Batch C as a constructed-interaction wave.
5. Run Batch E as a small metadata/rule cleanup wave.
6. In parallel, start Batch F data packs by source family.
7. Keep Batch G as a research-design lane, not a graduation sprint.

## Practical Near-Term Target

Near-term repair pool with plausible graduation potential:

- Batch A: 20
- Batch B: 10
- Batch C: 6
- Batch D: 19
- Batch E: 3

Total near-term candidate pool: `58`.

Realistic next-wave target: graduate `10-20` of those after focused repairs, then rerun the audit and repeat.
