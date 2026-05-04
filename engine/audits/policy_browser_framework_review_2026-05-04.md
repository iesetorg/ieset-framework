# Policy Browser and Framework Review - 2026-05-04

## Snapshot

- Hypotheses: 1479
- Diagnostic runs: 1474
- Policies indexed: 3029
- Policy cards with tested evidence: 2986
- Policy cards with no hypothesis link: 43
- Scoreboard claims: 2287 total, 2130 tested, 157 untested
- Tested-school range: 122 to 147

## Label Gaps

- Axis moves missing `intended`: 722
- Axis moves missing `magnitude`: 29
- Generic or ID-like policy titles: 455
- Policy statuses: {'candidate': 3029}
- Early coverage note: pre-1970 policies remain sparse compared with 1970-present coverage.

## Linkage Risks

- Link types: {'explicit': 49, 'inferred': 23880}
- Rows with at least one direct link: 39
- Rows only using inferred links: 2947
- Rows linked to all 17 schools: 2984
- Rows with no school links: 43

Most reused top hypotheses:
- `nordic_outcome_persistence_decomposition_v2`: 738 policy cards
- `chile_vs_venezuela_divergence_1999_2023`: 706 policy cards
- `fiscal_multipliers_zlb_higher_than_normal_regime`: 703 policy cards
- `el_salvador_bukele_gdp_crime_tradeoff_2019_2024`: 651 policy cards
- `japan_stagnation_wellbeing_outcomes`: 643 policy cards
- `estonia_market_reform_post_soviet_growth_1991_2007`: 600 policy cards
- `bukele_fdi_gdp_investment_climate_2019_2024`: 599 policy cards
- `italian_stagnation_decomposition_1999_2023`: 575 policy cards
- `fiscal_multipliers_state_dependent`: 571 policy cards
- `asian_convergence_vs_western_stagnation_2000_2023`: 544 policy cards

## Strengths

- Broad static evidence graph joins policies, hypotheses, movements, positions, axes, and run diagnostics into one publishable framework.
- Policy-browser coverage is high: 2,986 of 3,029 policy cards have tested linked evidence.
- The scoreboard has a large multi-school claim base with 2,130 tested claims across 17 schools.
- Run artifacts and preregistered hypothesis files make the framework auditable rather than just narrative.
- The browser now exposes direct versus inferred policy links, reducing hidden overclaim risk.

## Weaknesses

- Policy linkage is still too broad: many cards rely heavily on inferred analogues and 2,984 rows link all 17 schools, weakening school-specific interpretation.
- Labeling debt remains: 722 axis moves lack intended flags, 29 lack magnitude, and 455 policy titles are still ID-like or too generic.
- Policy status is not informative because all 3,029 policies are still marked candidate.
- Historical coverage is shallow before 1970 relative to the stated 1900-backfill ambition.
- Framework quality gates are not fully green yet: schema validation and preregistration timestamp checks still need repair from earlier audit runs.

## Recommended Next Levers

- Repair the 43 unlinked policy cards first, then require direct links for policy-browser "evidence" prominence.
- Backfill intended and magnitude fields on axes_moved, prioritising high-traffic fiscal and regulatory axes.
- Split policy-browser evidence into direct, inferred, and broad-school analogue sections instead of mixing them in one top-hypothesis list.
- Promote policy statuses beyond candidate: candidate, linked, tested, reviewed, contested, deprecated.
- Add decade and directness filters so users can isolate early-1900 policies and direct causal tests.
- Refresh README/methodology status after validation and preregistration repair so public claims match current corpus state.

## Unlinked Policy Examples

- `france_40_hour_week_1936`
- `france_associations_law_1901`
- `france_church_state_separation_1905`
- `france_matignon_agreements_1936`
- `france_paid_vacations_law_1936`
- `france_progressive_income_tax_1914`
- `france_sncf_nationalisation_1937`
- `france_weekly_rest_law_1906`
- `france_workers_peasants_pensions_1910`
- `germany_employee_insurance_act_1911`
- `germany_reich_insurance_code_1911`
- `germany_tariff_act_1902`
- `germany_wehrbeitrag_army_bill_1913`
- `india_constitution_1950`
- `india_government_of_india_act_1919`
- `india_government_of_india_act_1935`
- `india_indian_councils_act_1909`
- `india_industrial_policy_resolution_1948`
- `india_planning_commission_establishment_1950`
- `india_reserve_bank_of_india_act_1934`
- `italy_acerbo_law_1923`
- `italy_banking_law_1936`
- `italy_carta_del_lavoro_1927`
- `italy_daneo_credaro_school_law_1911`
- `italy_ina_life_insurance_monopoly_1912`
