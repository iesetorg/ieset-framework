# Monthly Hypothesis Factory, Scoreboard Tally, And Swarm Spec - 2026-05-12

## Local Verdict Inventory

Local run diagnostics currently contain 1,568 parsed diagnostics files:

- `PARTIAL`: 767
- `SUPPORTED`: 450
- `INCONCLUSIVE_DATA_PENDING`: 199
- `REFUTED`: 149
- `UNKNOWN`: 3

This is the verdict inventory, not the scoreboard. The scoreboard only moves when a verdict passes mapping, interpretation, duplicate, and scope checks.

## Latest Mapped Scoreboard

Newest mapped audit: `engine/audits/scoreboard_prediction_outcome_audit_2026-05-12_after_mapping_wave1.md`.

| School | Signal | Q-net | Raw net | Tested | Supports | Refutes | Untested |
|---|---|---:|---:|---:|---:|---:|---:|
| `chicago_monetarism` | positive_signal | 20.8 | 34.5 | 124 | 32 | 12 | 8 |
| `ordoliberal` | positive_signal | 16.5 | 28.0 | 139 | 35 | 18 | 8 |
| `austrian` | positive_signal | 16.2 | 26.5 | 128 | 31 | 17 | 6 |
| `classical_liberal` | positive_signal | 15.2 | 23.5 | 154 | 38 | 25 | 9 |
| `developmentalism` | positive_signal | 11.0 | 41.5 | 124 | 43 | 4 | 9 |
| `new_keynesian` | too_close_to_call | 5.0 | 13.5 | 119 | 14 | 7 | 13 |
| `empirical_pragmatist` | too_close_to_call | 4.8 | 7.5 | 123 | 12 | 7 | 8 |
| `institutionalism` | too_close_to_call | 3.4 | 10.0 | 122 | 12 | 6 | 11 |
| `mmt` | too_close_to_call | -1.1 | 5.5 | 122 | 26 | 18 | 12 |
| `marxist_leninist` | too_close_to_call | -1.6 | 4.0 | 120 | 21 | 16 | 15 |
| `post_keynesian` | too_close_to_call | -1.8 | 3.5 | 121 | 25 | 19 | 12 |
| `eco_socialist` | too_close_to_call | -2.1 | 5.5 | 120 | 24 | 18 | 16 |
| `marxian` | too_close_to_call | -2.9 | 0.0 | 122 | 22 | 22 | 14 |
| `democratic_socialist` | too_close_to_call | -3.4 | 1.5 | 122 | 22 | 20 | 17 |
| `social_democratic` | too_close_to_call | -3.4 | 1.5 | 121 | 21 | 18 | 12 |
| `market_socialist` | too_close_to_call | -3.9 | 1.5 | 119 | 21 | 19 | 16 |
| `degrowth` | too_close_to_call | -4.8 | -3.5 | 119 | 13 | 15 | 14 |

Interpretation: market-liberal and ordoliberal clusters have positive mapped signal. Developmentalism remains positive but should be balanced with longer-horizon and frontier-prosperity tests. Most heterodox/state/welfare/ecological schools are not losing decisively; they are mostly inside the no-call band and need better, less blunt tests.

## Cross-School 50 Status

The latest cross-school 50 wave was cleaned after swarm verification:

- 50 hypotheses, 50 steelmen, 50 run directories.
- Verdict tally: 13 `SUPPORTED`, 25 `PARTIAL`, 12 `REFUTED`.
- Invalid World Bank aggregate region codes were removed via a real ISO3 allowlist.
- All generated samples now use full filtered country lists.
- Diagnostics no longer list the outcome as its own control.
- Targeted `cross_school_*` schema scan produced no matching errors.
- Scope validation: 2313 pass, 0 errors, 6 warnings.

These 50 are not automatically scoreboard-converted. They are a cleaned verdict inventory awaiting careful mapping and duplicate/broad-panel QA.

## Factory Operating Target

The monthly factory must optimize for verdict throughput and conversion throughput.

Daily targets:

- Normal day: 60 attempted runs, 25-40 conversion decisions.
- Templated day: up to 90 attempted runs if the runner family is already validated.
- Stop a lane if inconclusive/data-pending exceeds 25% for two consecutive batches.
- Never let unmapped verdict inventory exceed two days of new verdicts.

Monthly target:

- Raw verdict target: 920-1,350 attempted/verdict-bearing results.
- Scoreboard-ready target: 500-810 mapped results.
- Practical expectation: 500+ scoreboard-ready verdicts if conversion keeps pace.

## Role Split

1. Queue boss: chooses daily tracks, source freeze, batch IDs, and yield targets.
2. Spec promoter: writes runnable specs with plain-English claims and falsification rules.
3. Runner: executes 20-30 item batches and writes diagnostics/result cards/evidence artifacts.
4. QA mapper: assigns each verdict to ready, needs mapping, hold, or repair.
5. Data repair: handles source aliases, missing manifests, API limits, and blocked family repairs.
6. Scoreboard steward: recomputes only after validations and writes swing logs.

## Scoreboard Conversion Rules

Every future verdict gets one bucket before mapping:

- `scoreboard_ready_existing_mapping`
- `needs_position_claim_mapping`
- `hold_interpretation_qa`
- `hold_duplicate_broad_panel_qa`
- `hold_broad_panel_upgrade`
- `repair_data_or_design`

Required mapping fields:

- position-side `linked_hypothesis_id`
- `school_prediction`
- `claim_polarity`
- hypothesis-side reciprocal `covers_claims`

Partial verdict discipline:

- Neutral partial: score impact 0.
- Directional partial: score impact 0.5, evidence-weighted.
- Ambiguous partial: hold in interpretation QA.

Concentration rules:

- Associational panels remain q-weight 0.5.
- Associational panels should not contribute more than 50% of new daily q-weight.
- No single broad panel family should contribute more than 25% of daily q-weight.
- Max 4 net-new scored links per school per daily mapping wave.
- Prioritize schools below the median tested count.

Daily swing log must record:

- reviewed / accepted / held / repaired counts
- new links by school
- q-net and raw-net before/after
- top school swings
- duplicate fingerprints introduced or cleared
- partials scored directional versus neutral
- associational share of new q-weight

## First-Month Data-Ready Backlog

Best first sequence: batches 1, 3, 6, 7, 8, and 9. These use the freshest landed data and replace blunt macro proxies with direct credit, productivity, energy, welfare, labour, and minimum-wage designs.

### Batch 01: BIS Credit Cycle / Austrian-Minsky Macro

1. `bis_credit_gap_house_price_reversal_oecd_1970_2025`
2. `bis_credit_gap_unemployment_lag_panel_1970_2025`
3. `bis_credit_gap_dsr_joint_fragility_panel_1999_2025`
4. `bis_household_dsr_consumption_slowdown_panel_1999_2025`
5. `bis_corporate_dsr_investment_slowdown_panel_1999_2025`
6. `bis_credit_gap_current_account_twin_deficit_risk`
7. `bis_credit_gap_low_real_rate_amplifier_panel`
8. `bis_house_price_credit_gap_boom_bust_panel`
9. `bis_credit_gap_private_investment_reversal_panel`
10. `bis_long_horizon_credit_cycle_market_discipline_panel`

### Batch 03: OECD Productivity / Frontier Convergence

21. `oecd_pdb_gdp_hour_frontier_convergence_1950_2025`
22. `oecd_pdb_tfp_growth_frontier_persistence_1970_2025`
23. `oecd_pdb_capital_deepening_without_tfp_limit`
24. `oecd_pdb_investment_share_tfp_interaction_panel`
25. `oecd_pdb_small_open_economy_frontier_convergence`
26. `oecd_pdb_market_reform_productivity_compounder`
27. `oecd_pdb_tax_wedge_productivity_growth_panel`
28. `oecd_pdb_hours_reduction_output_tradeoff_panel`
29. `oecd_pdb_post_2008_productivity_hysteresis_panel`
30. `oecd_pdb_public_sector_share_productivity_drag`

### Batch 06: Eurostat Energy Prices / Nuclear Transition

51. `eurostat_industrial_electricity_price_manufacturing_va_2007_2025`
52. `eurostat_household_electricity_price_consumption_panel`
53. `eurostat_electricity_price_inflation_pass_through`
54. `eurostat_nuclear_retention_industrial_price_panel`
55. `eurostat_renewable_share_electricity_price_transition_cost`
56. `eurostat_energy_price_household_distribution_stress`
57. `eurostat_energy_price_export_competitiveness_panel`
58. `eurostat_energy_price_unemployment_regional_panel`
59. `eurostat_electricity_price_volatility_industrial_exit`
60. `eurostat_energy_price_services_vs_industry_reallocation`

### Batch 07: OECD SOCX / Welfare Architecture

61. `oecd_socx_automatic_stabiliser_output_loss_panel_1980_2024`
62. `oecd_socx_unemployment_benefits_duration_panel`
63. `oecd_socx_active_vs_passive_labour_policy_unemployment`
64. `oecd_socx_public_social_spending_employment_tradeoff`
65. `oecd_socx_family_benefits_fertility_housing_interaction`
66. `oecd_socx_old_age_spending_growth_tradeoff`
67. `oecd_socx_disability_spending_lfp_tradeoff`
68. `oecd_socx_poverty_elasticity_programme_mix_panel`
69. `oecd_socx_tax_wedge_employment_compatibility_panel`
70. `oecd_socx_open_economy_welfare_compatibility_panel`

### Batch 08: OECD EPL / Low-Skill Labour

71. `oecd_epl_low_education_unemployment_panel_1985_2019`
72. `oecd_epl_youth_unemployment_panel_1985_2019`
73. `oecd_epl_temporary_contract_dualism_panel`
74. `oecd_epl_productivity_growth_moderation_panel`
75. `oecd_low_education_unemployment_minimum_wage_bite`
76. `oecd_low_education_unemployment_union_density_panel`
77. `oecd_low_education_unemployment_productivity_shield`
78. `oecd_activation_spending_low_education_unemployment`
79. `oecd_socx_minimum_wage_low_skill_tradeoff_panel`
80. `oecd_epl_growth_shock_unemployment_persistence_panel`

### Batch 09: US Minimum Wage / BLS State-County Design

81. `bls_qcew_county_food_service_minimum_wage_growth`
82. `bls_qcew_state_food_service_minimum_wage_growth`
83. `bls_qcew_county_food_service_wage_floor_border_design`
84. `bls_qcew_food_service_small_county_sensitivity`
85. `bls_qcew_food_service_recession_interaction`
86. `bls_qcew_food_service_post_covid_recovery_wage_floor`
87. `bls_oews_median_bite_food_service_employment_panel`
88. `bls_oews_p10_bite_food_service_employment_panel`
89. `bls_minimum_wage_bite_state_total_employment_panel`
90. `bls_minimum_wage_bite_low_tail_threshold_panel`

## Remaining Backlog Families

- BIS FX / external competitiveness.
- OECD PDB wage/productivity decoupling.
- Eurostat sectoral reallocation.
- ILO labour / migration / demography.
- IRENA renewables learning curves.
- FAOSTAT agriculture and food security.
- Fraser EFW with more direct outcomes.
- Mobility, housing, and education channels.

The full read-only backlog from the swarm contains 140 named hypotheses across 14 batches.

## 30-Day Policy Data Acquisition Spec

Priority data spine:

1. OECD SDMX spine: STAN, Global Revenue Statistics, fossil-fuel support.
2. WITS / UNCTAD TRAINS tariffs.
3. UN Comtrade curated trade flows.
4. IMF GFS plus OECD Revenue.
5. UNIDO INDSTAT plus STAN plus EU/wiiw KLEMS bridge.
6. IEA/OECD/IMF energy subsidy data.
7. Enterprise Surveys plus B-READY.

Schedule:

- Days 1-3: canonical acquisition contract and row-level provenance rules.
- Days 4-8: OECD SDMX spine.
- Days 9-13: WITS / TRAINS tariff layer.
- Days 14-17: curated Comtrade pull and derived trade-exposure measures.
- Days 18-21: fiscal architecture with IMF GFS and OECD Revenue.
- Days 22-24: industrial productivity bridge.
- Days 25-27: energy subsidy layer.
- Days 28-30: Enterprise Surveys / B-READY indicators.

Guardrails:

- Pull curated slices before full universes.
- Preserve native frequency and units.
- Separate policy treatment variables from outcome variables.
- Every derived variable needs a reproducible recipe and source-cell lineage.
- Treat STAN/KLEMS vintage breaks as quality flags.

## Immediate Next Move

Start with Batch 01 BIS credit-cycle hypotheses and run it in two 5-case passes or one 10-case pass. In parallel, start the OECD SDMX data spine because it unlocks productivity, tax, sector, and subsidy tracks at once.
