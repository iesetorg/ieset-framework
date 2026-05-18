# May 19 Swarm Cleanup And Scoreboard Mapping Gate

Generated: 2026-05-19

## Scope

This pass reviewed the May 19 swarm throughput wave after commit `0da70bba` and recomputed the public scoreboard with the current reciprocal claim links.

Known unrelated loose files remain excluded from this cleanup:

- `web/app/scoreboard/page.tsx`
- `data/manifests/fetch_run_2026-05-17T231721Z.yaml`
- `data/manifests/fetch_run_2026-05-17T231736Z.yaml`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`

## Mapping Decision

New reciprocal scoreboard mappings applied in this pass: **0**.

That is intentional. The wave produced useful run artifacts, but the unmapped subset does not yet clear the mapping gate. The clean scoreboard action is to keep the existing reciprocal links, recompute the audit, and hold the duplicate or proxy-first material until upgraded.

Current recompute:

- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-19_after_swarm_cleanup.json`
- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-19_after_swarm_cleanup.md`

The recompute finds 2,309 public claim links.

## Already Scoreboard-Mapped From The Reviewed Wave

These reviewed artifacts already have reciprocal position-side links and hypothesis-side `covers_claims`. No duplicate claim links were added.

| hypothesis | verdict posture | mapping posture |
| --- | --- | --- |
| `firm_entry_rate_long_run_productivity` | supported, but evidence packet is incomplete | keep existing links; prioritize evidence-packet repair before treating as fresh decisive support |
| `chile_market_reform_long_horizon_with_democracy` | partial | already mapped to long-horizon market-reform claims |
| `canada_market_liberalisation_vs_state_industry_1988_2024` | partial | already mapped to long-horizon liberalisation claims |
| `regulatory_predictability_cross_sector_investment` | refuted | already mapped to rules-and-investment claims |
| `tax_inequality_korea_progressive_turn_2017_2020` | inconclusive data-pending | already linked, but not score-moving while public verdict is untested |
| `industrial_policy_high_governance_success` | partial | already mapped to industrial-policy/state-capacity claims |
| `rent_control_reduces_housing_supply_and_quality` | blocked | already linked, but not score-moving while blocked |
| `price_controls_produce_shortages_and_quality_degradation` | inconclusive data-pending | already linked, but not score-moving while untested |
| `tcja_2017_growth_effect` | weakened | already mapped narrowly to the TCJA/New Keynesian mixed claim |
| `colonial_institutions_post_independence_growth` | inconclusive data-pending | already linked, but not score-moving while untested |
| `chile_post_1990_institutional_premium` | inconclusive data-pending | already linked, but not score-moving while untested |

## Held From Scoreboard Conversion

| group | affected hypotheses | reason held | next safe action |
| --- | --- | --- | --- |
| incomplete Worker A packets | `pension_forced_saving_capital_deepening`, `politicised_credit_election_cycle_growth_drag` | missing preregistered series and incomplete evidence packets | fetch/construct the missing pension, credit, election-cycle, capital-deepening, and terms-of-trade series, then rerun |
| WGI regulatory-quality to WGI corruption proxy cluster | `procurement_competition_corruption`, `licensing_discretion_bribery`, `rule_bound_regulation_business_trust`, `crony_capitalism_not_market_freedom`, `market_governance_qol_broad_scope` | same broad proxy fingerprint, same coefficient/p-value pattern, not independent scoreboard evidence | consolidate as one meta-screen or rebuild child tests with direct procurement, licensing, trust, and crony-allocation datasets |
| WGI institutional partial screens | `market_reform_civil_liberties_interaction`, `market_freedom_democratic_resilience`, `intervention_qol_corruption_interaction`, `federalism_market_experimentation`, `economic_freedom_personal_freedom`, `property_rights_median_income_growth_1980_2024`, `state_ownership_media_freedom` | partial/no-call verdicts on proxy-first designs | use as data-gap guides, not scoreboard claims, until a direct treatment/outcome design produces a directional verdict |
| Heritage WGI/WDI panel variants | Worker D and Worker E `heritage_*_wgi*panel` runs | manifests or audits mark them as not scoreboard-eligible pending duplicate/design review | promote only after explicit pre-registration, duplicate review, and a non-Heritage-screen treatment rationale |
| blocker and inconclusive repairs | `rent_control_reduces_housing_supply_and_quality`, `price_controls_produce_shortages_and_quality_degradation`, `colonial_institutions_post_independence_growth`, `chile_post_1990_institutional_premium`, `tax_inequality_korea_progressive_turn_2017_2020` | useful blocker maps but not tested public verdicts | acquire the missing direct data before any mapping expansion |

## Scoreboard Snapshot After Cleanup

No new mapping swing was introduced by this cleanup pass. The current ranked q-net leaders in the recompute are:

| school | q-net | raw net | tested |
| --- | ---: | ---: | ---: |
| `chicago_monetarism` | 23.1 | 39.5 | 135 |
| `classical_liberal` | 20.1 | 32.0 | 179 |
| `ordoliberal` | 20.1 | 34.5 | 152 |
| `austrian` | 17.4 | 30.5 | 134 |
| `developmentalism` | 14.0 | 46.5 | 143 |

`empirical_pragmatist` is treated as a benchmark control in the audit script, not as a ranked ideological school.

## Repair Queue Before Next Mapping Wave

1. Repair incomplete evidence packets for `firm_entry_rate_long_run_productivity`, `pension_forced_saving_capital_deepening`, and `politicised_credit_election_cycle_growth_drag`.
2. Collapse the WGI proxy cluster into one non-scoreboard meta-screen, or rebuild it with direct procurement/licensing/business-trust/corruption datasets.
3. Choose the two best Heritage Worker E candidates for a clean pre-registration pass: `heritage_economic_freedom_life_expectancy_wgi_composite_panel` and `heritage_business_freedom_private_consumption_pc_wgi_rq_panel`.
4. Continue data acquisition for the blocked direct-policy surfaces: rent control, price controls, colonial institutions, and Korea progressive-tax synth coverage.
5. Only after those repairs, append reciprocal position claims and hypothesis-side `covers_claims` in a small batch, then rerun `validate_link_reciprocity.py` and `audit_scoreboard_outcomes.py`.
