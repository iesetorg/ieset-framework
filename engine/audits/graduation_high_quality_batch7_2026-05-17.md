# High-quality graduation batch 7 - 2026-05-17

This batch followed the control-fixed scoreboard audit and deliberately tested the current
preflight-ready queue rather than adding broad, low-signal claims. It also exposed a
useful quality problem: many entries that are loader-ready are not yet estimand-ready.

## UI/audit cleanup

- Removed the human-facing `signal` column from `scripts/audit_scoreboard_outcomes.py`.
- Kept signal fields in the JSON audit for programmatic consumers.
- Recomputed `engine/audits/scoreboard_prediction_outcome_audit_2026-05-17_unblocking_batch_control_fixed.md`.

## Queue state before reruns

The current preflight audit reported 52 preflight-ready inconclusive runs:

| State | Count |
| --- | ---: |
| preflight-ready | 52 |
| preflight-blocked | 66 |
| unknown-template | 37 |
| missing-spec-vars | 8 |
| stub-rule | 3 |

## Rerun slice

25 candidates were tried across lower-risk templates first:

- Descriptive: 4
- Event study: 6
- Local projections: 2
- DiD / Callaway-Santanna: 5
- Panel FE: 8

`productivity_compensation_decoupling_post_1973` was intentionally skipped because
batch 5 established that the local BLS vintages do not contain the required 1973 and
2019 endpoints.

## Graduated artifacts

| Hypothesis | Verdict | Main result | Quality note |
| --- | --- | --- | --- |
| `abenomics_monetary_policy_demand_effect` | REFUTED | Event-study/ITS gap has the opposite sign to the claim: mean post gap `+7.485`, `z=+25`. | Real artifact, but the YAML falsification prose still contains a stub sentence and should be sharpened before public-grade scoreboard use. |
| `universal_vs_meanstest_child_poverty` | PARTIAL | Panel FE coefficient `-4.874e-21`, `p=0.0608`; effect magnitude effectively zero. | Real artifact, but the preferred OECD child-poverty and derived regime vintages are missing, so treat as research-grade until those land. |

Replication wrappers were backfilled for both:

- `engine/runs/abenomics_monetary_policy_demand_effect/replication.py`
- `engine/runs/universal_vs_meanstest_child_poverty/replication.py`

## Non-graduating attempts

### Insufficient pre/post or sample observations

- `demo_germany_gastarbeiter_long_run`
- `friedman_schwartz_great_depression_monetary_cause`
- `great_depression_over_accumulation_vs_monetary_cause`
- `welfare_pension_mexico_universal_2023_fiscal_effect`
- `corbyn_manifesto_capital_flight_prediction`
- `fed_qt_balance_sheet_unwind_2022_2025_market_response`
- `macron_labour_tax_employment_distribution`
- `mena_egypt_floatation_episodes_2016_2024`
- `welfare_reform_uk_universal_credit_employment_effect`
- `fed_2022_rate_cycle_inflation_response_lag`
- `welfare_transfer_hong_kong_cash_payout_2020`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `competition_enforcement_consumer_welfare_effect`

### Listwise-deletion collapse in DiD

- `child_benefit_expansion_child_poverty_effect`
- `chips_act_2022_semiconductor_capacity_2024_2027`
- `welfare_transfer_china_dibao_rural_pension_2009`
- `welfare_transfer_indonesia_pkh_blt_2007_2022`
- `welfare_transfer_kenya_hsnp_2015_consumption_smoothing`

### No within-country FE treatment variation

- `china_soe_vs_cee_privatised_growth`
- `protected_infant_industries_fail_to_mature`
- `consumer_choice_variety_trade_market_reform`
- `demo_canada_points_system_immigration`
- `gfc_balance_sheet_recession_post_2008_household_dual_mandate`

## Method lesson

The old preflight rule is too permissive. It asks whether sources load, but it does
not fully check the estimation surface. Before the next large wave, add a stricter
graduation preflight that checks:

- minimum post-filter/listwise observations for each template
- minimum pre/post counts for event/descriptive designs
- within-entity treatment variation when entity fixed effects are enabled
- whether the runner is testing the registered gate rather than a generic proxy

## Preflight repair applied

`scripts/rerun_preflight_ready_inconclusive.py` was tightened after this batch:

- Panel FE now checks listwise sample size and FE treatment variation.
- DiD now checks listwise sample size plus treated/control support.
- Local projections now enforce the 50-observation minimum.
- Descriptive/event-study specs now check the same pre/post minimums as the runners.
- Synth-DiD now checks treated/donor pre-period and post-period overlap.

The stricter audit reduced the queue from 52 apparent candidates to 20, and then
to 2 after synth-DiD donor/pre-period checks. The last 2 were manually rerun and
still blocked:

- `high_income_escape_market_openness_1950_2024`: insufficient observations after listwise deletion (`8`).
- `zimbabwe_land_reform_cause_decomposition`: insufficient observations after listwise deletion (`0`).

The practical result is that the generic rerun queue is exhausted for high-quality
purposes. The next wave should be repair-led, not brute-force reruns.

## Next best high-quality levers

1. Build exact-gate evaluators for the Great Depression monetary/over-accumulation pair instead of generic pre/post descriptive scoring.
2. Load OECD child-poverty and child-benefit-regime vintages for the universal-vs-means-tested child-poverty result.
3. Convert static-treatment panel-FE candidates to event-study, synth-DiD, or explicit before/after threshold designs where appropriate.
4. Build missing donor/pre-period coverage for the labour-reform synth-DiD cases before rerunning them.
5. Add a diagnostics-reason gate to the preflight audit if the last two false positives keep resurfacing after data-refresh checks.
