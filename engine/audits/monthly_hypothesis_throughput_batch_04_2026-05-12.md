# Monthly Hypothesis Throughput Batch 04

Date: 2026-05-12

Purpose: continue the monthly hypothesis throughput plan in 30-run batches, while repairing older runner-wrapper imports encountered during execution.

## Summary

- Runs attempted: 30
- Verdict-bearing results: 25
- Supported: 7
- Partial: 17
- Refuted: 1
- Inconclusive data/model-pending: 5

## Wrapper Repair

Five initial runs failed because older wrappers imported runner modules as `scripts.*`, which is shadowed on this machine by an installed third-party `scripts` package. A mechanical hygiene pass updated 47 wrappers to add the repository `scripts/` directory directly to `sys.path` and import the runner module by filename. The five affected Batch 04 runs were then rerun.

## Results

| Hypothesis | Result |
| --- | --- |
| `CBDC_design_privacy_tradeoff` | partial |
| `abenomics_monetary_fiscal_coordination_effect` | inconclusive data/model-pending |
| `absolute_decoupling_global_material_throughput` | supported |
| `active_labour_market_policy_conditionality_works` | partial |
| `africa_botswana_diamond_dependency_post_2014` | partial |
| `africa_ethiopia_gerd_economic_effect_2011_2024` | partial |
| `africa_ethiopia_tigray_war_economic_collapse_2020_2022` | partial |
| `africa_ghana_imf_program_2022_debt_distress` | partial |
| `africa_kenya_mpesa_digital_payments_formalisation_2007_2024` | inconclusive data/model-pending |
| `africa_mauritius_export_zone_model_1980_2024` | partial |
| `africa_nigeria_fuel_subsidy_removal_2023` | inconclusive data/model-pending |
| `africa_nigeria_naira_redesign_2023_cash_crisis` | partial |
| `africa_rwanda_post_genocide_growth_model_1995_2024` | partial |
| `africa_south_africa_load_shedding_manufacturing_2007_2024` | partial |
| `africa_ssa_post_covid_recovery_divergence_2020_2024` | refuted |
| `agricultural_export_ban_price_instability` | partial |
| `agricultural_trade_liberalisation_food_security` | partial |
| `albania_growth_health_services_shift_1990_2023` | supported |
| `apprenticeship_employer_chamber_quality` | partial |
| `argentina_cepo_lift_2015_fx_inflation_reserves` | supported |
| `argentina_default_collapse_output_effects` | partial |
| `argentina_fx_obligation_inflation_mechanism` | supported |
| `argentina_institutional_instability_decline` | inconclusive data/model-pending |
| `argentina_paso_2019_fx_reserves_inflation_base_money_lag` | supported |
| `argentina_peronism_recurring_fiscal_inflation_cycle_1945_2023` | partial |
| `armenia_growth_health_services_shift_1990_2023` | supported |
| `asia_japan_abenomics_retrospective_2013_2023` | supported |
| `asia_korea_chaebol_reform_2017_2024` | partial |
| `asia_pakistan_imf_programme_cycle_1988_2024` | inconclusive data/model-pending |
| `asia_sri_lanka_default_2022_imf_2023` | partial |

## Repair Queue

- `abenomics_monetary_fiscal_coordination_effect`: event-study runner returned inconclusive; inspect missing variables/window.
- `africa_kenya_mpesa_digital_payments_formalisation_2007_2024`: insufficient pre-period coverage.
- `africa_nigeria_fuel_subsidy_removal_2023`: Nigeria missing from the current synthetic-DID panel.
- `argentina_institutional_instability_decline`: checklist produced no resolved metrics.
- `asia_pakistan_imf_programme_cycle_1988_2024`: treatment absorbed under current country fixed-effects setup.

## QA Notes

- Batch 04 is case-study heavy, so partial verdicts often mean the direction or placebo/permutation threshold is not strong enough for a decisive call, not that the run failed.
- National event-window results such as the Argentina FX shocks are strong timing/magnitude tests but should be labelled as compact event evidence rather than broad structural causal proof.
