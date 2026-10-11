# Sparse-school registered rerun cohort — 2026-10-11

This is a **blocked engineering queue**, not a conversion or an increase in tested school coverage. METHODOLOGY.md defines registration as a hypothesis file committed before its first run; this queue follows that rule, then separately records whether its YAML status was explicitly `pre_registered` at that time. It checks scoring-relevant current fields against the original committed specification.

**20 timing-verified hypotheses / 61 school links / 0 ready to score.** Only 2 studies / 14 school links had explicit `pre_registered` status before running; the others were draft or candidate and need design-completeness review. 7 retain an intact frozen design; 13 changed scoring-relevant fields after first registration.

| School | Directional scored now | Timing-verified rerun queue | Explicit prereg status | If queued cases later clear | Remaining to 200 | Ready now |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `social_democratic` | 1 | 14 | 0 | 15 | 185 | 0 |
| `democratic_socialist` | 0 | 9 | 2 | 9 | 191 | 0 |
| `post_keynesian` | 0 | 11 | 2 | 11 | 189 | 0 |
| `mmt` | 1 | 3 | 2 | 4 | 196 | 0 |
| `new_keynesian` | 0 | 5 | 0 | 5 | 195 | 0 |
| `degrowth` | 0 | 0 | 0 | 0 | 200 | 0 |
| `market_socialist` | 1 | 3 | 2 | 4 | 196 | 0 |
| `marxian` | 0 | 3 | 2 | 3 | 197 | 0 |
| `marxist_leninist` | 0 | 9 | 2 | 9 | 191 | 0 |
| `eco_socialist` | 0 | 4 | 2 | 4 | 196 | 0 |

## Case actions

| Hypothesis | Status before run | Schools | Original-spec drift | Current public blocker | Next action |
| --- | --- | --- | --- | --- | --- |
| `active_labour_market_policy_conditionality_works` | `draft` | post_keynesian | sample, falsification | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `apprenticeship_employer_chamber_quality` | `draft` | post_keynesian | sample, falsification | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `australia_hawke_keating_reform_long_run` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | claim, sample, variables, estimator, falsification, prior_confidence | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `canada_market_liberalisation_vs_state_industry_1988_2024` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | claim, sample, variables, estimator, falsification, prior_confidence | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `carbon_tax_revenue_neutral_double_dividend` | `draft` | eco_socialist | sample, falsification | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `contract_enforcement_fdi_productivity_spillovers` | `candidate` | new_keynesian, social_democratic | variables | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `corruption_state_allocation_growth_interaction` | `candidate` | new_keynesian, social_democratic | none | external_integrity_quarantine | `integrity_source_review` |
| `firm_entry_rate_long_run_productivity` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | variables | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `frontier_income_volatility_state_allocation` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | variables | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `government_consumption_share_tfp` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | none | external_integrity_quarantine | `integrity_source_review` |
| `industrial_policy_high_governance_success` | `candidate` | new_keynesian, social_democratic | variables | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `judicial_independence_growth_persistence` | `candidate` | new_keynesian, social_democratic | none | estimator_floor_failed | `source_and_full_rule_estimator_repair` |
| `labour_flexibility_security_complement` | `candidate` | new_keynesian, social_democratic | none | estimator_floor_failed | `source_and_full_rule_estimator_repair` |
| `oecd_pdb_hours_reduction_output_tradeoff_panel` | `candidate` | social_democratic | none | audit_quarantined_pending_v2 | `independent_v2_review` |
| `uk_thatcher_market_reform_40yr_services_frontier` | `candidate` | democratic_socialist, marxist_leninist, post_keynesian, social_democratic | claim, sample, variables, estimator, falsification, prior_confidence | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `unemployment_benefit_duration_long_term_unemployment` | `draft` | democratic_socialist, eco_socialist, market_socialist, marxian, marxist_leninist, mmt, post_keynesian | sample, falsification | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `unemployment_benefit_generosity_employment_drag` | `pre_registered` | democratic_socialist, eco_socialist, market_socialist, marxian, marxist_leninist, mmt, post_keynesian | none | external_integrity_quarantine | `integrity_source_review` |
| `welfare_architecture_market_openness_nordic` | `candidate` | social_democratic | variables, estimator, falsification | external_integrity_quarantine | `review_first_committed_spec_or_register_new_id` |
| `welfare_state_market_flexibility_complement` | `candidate` | social_democratic | variables | estimator_floor_failed | `review_first_committed_spec_or_register_new_id` |
| `workfare_conditionality_employment_effect` | `pre_registered` | democratic_socialist, eco_socialist, market_socialist, marxian, marxist_leninist, mmt, post_keynesian | none | external_integrity_quarantine | `integrity_source_review` |

## Case-specific repair screens

- `corruption_state_allocation_growth_interaction`: The design is unchanged, but the external integrity hold requires source and result custody review.
- `government_consumption_share_tfp`: The design is unchanged, but the external integrity hold requires source and result custody review.
- `judicial_independence_growth_persistence`: The saved fallback does not load the registered V-Dem judicial composite or v2x_jucon; acquire those inputs and fit the frozen primary model.
- `labour_flexibility_security_complement`: The saved fallback lacks OECD EPL and union-density inputs and does not test the registered security interaction.
- `oecd_pdb_hours_reduction_output_tradeoff_panel`: The frozen hours-growth coefficient and support gate have the wrong sign for the English no-output-loss claim. Keep v1 quarantined; a new ID needs a signed equivalence or noninferiority estimand and independent holdout.
- `unemployment_benefit_generosity_employment_drag`: First committed as pre_registered. Later country-list deduplication did not change the frozen sample; its saved run remains externally quarantined. Replay the full original rule with claim-matched sources before judging feasibility.
- `workfare_conditionality_employment_effect`: First committed as pre_registered. Later country-list deduplication did not change the frozen sample; its saved run remains externally quarantined. Replay the full original rule with claim-matched sources before judging feasibility.

## Gates before any claim can score

1. Review the first committed spec for a complete frozen design. Replay that design if valid, or commit a new ID and independent holdout. Changed current fields are not retroactive preregistration.
2. Obtain the declared source vintage and construct claim-matched variables. Reject generic GDP/EFW fallback regressions and estimator warnings.
3. Execute the full frozen falsification rule with replication, then rebuild the evidence-tier ledger and school audit. Resolve every integrity/quarantine hold before publication.
4. Add genuinely new school-specific claims for gaps this cohort cannot fill, especially Degrowth, only after their data and future holdout contracts are specified.

The 61 queued school links are overlapping predictions about 20 studies, not independent studies. Even if all later pass, each school remains far short of 200 directional scored tests.
