# Duplicate Broad-Panel Upgrade Plan (2026-05-12)

Purpose: convert the next wave of throughput verdicts without letting duplicated broad-panel screens overstate the scoreboard.

## Summary

- Held duplicate broad-panel items: 18
- Duplicate fingerprint groups: 5
- Near-term upgrades: none
- Data-gap upgrades: occupational_licensing_income_mobility
- Do-not-score-directly items: market_governance_qol_broad_scope, qol_anomaly_weight_broad_scope_test

## Duplicate Groups

- `coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero` (5): `CBDC_design_privacy_tradeoff`, `active_labour_market_policy_conditionality_works`, `agricultural_export_ban_price_instability`, `agricultural_trade_liberalisation_food_security`, `apprenticeship_employer_chamber_quality`
- `coef=+0.205 (sign matches claim +), p=0.0329` (4): `crony_capitalism_not_market_freedom`, `market_governance_qol_broad_scope`, `procurement_competition_corruption`, `licensing_discretion_bribery`
- `coef=+3078 (sign matches claim +), p=0.00422` (3): `qol_anomaly_weight_broad_scope_test`, `occupational_licensing_income_mobility`, `labor_reform_real_wage_growth`
- `coef=+3078 (sign opposite claim -), p=0.00422` (3): `price_signal_integrity_qol_panel`, `market_institution_duration_qol_persistence`, `market_reform_inflation_adjusted_wages`
- `coef=-0.3453 (sign matches claim -), p=0.0312` (3): `intervention_reversal_qol_loss_1980_2024`, `intervention_intensity_qol_volatility_1970_2024`, `campaign_favoritism_subsidy_allocation`

## Upgrade Queue

### 2. `occupational_licensing_income_mobility`

- Verdict: SUPPORTED — coef=+3078 (sign matches claim +), p=0.00422
- Decision: data_gap_then_upgrade
- Problem: The present test measures GDP per capita against WGI RQ, not occupational licensing or mobility.
- Upgrade: Rebuild with a direct licensing-burden treatment and a mobility/wage outcome.
- Scoreboard rule: Eligible only after direct licensing treatment and mobility/labour outcome are present.
- Candidate data: US state occupational licensing coverage or license burden panels, OECD PMR professional-services restrictions, IPUMS/CPS wage mobility or employment transitions, Opportunity Atlas / Chetty mobility measures for US geography
- Local availability: OECD PMR professional-services restrictions are available as a partial licensing proxy.; A direct mobility/wage-transition outcome is not yet confirmed locally.

### 3. `market_governance_qol_broad_scope`

- Verdict: SUPPORTED — coef=+0.205 (sign matches claim +), p=0.0329
- Decision: split_or_demote_to_meta_screen
- Problem: The claim is intentionally broad and currently duplicates the same WGI corruption/regulatory-quality panel as the corruption hypothesis.
- Upgrade: Split into narrower outcome-specific hypotheses or keep as a meta-audit that summarizes independent tests rather than scoring directly.
- Scoreboard rule: Do not convert the broad parent directly; score only child tests with distinct datasets.
- Candidate data: one governance-specific child test, one income or life-expectancy child test, one business dynamism or investment child test
- Local availability: Use existing verdict inventory and local WDI/WGI/V-Dem/PMR panels to build child tests; do not reuse this broad parent as direct evidence.

### 4. `qol_anomaly_weight_broad_scope_test`

- Verdict: SUPPORTED — coef=+3078 (sign matches claim +), p=0.00422
- Decision: demote_to_meta_audit
- Problem: This is a framework-level anomaly-weight claim, but the current run is just a GDP-per-capita/WGI RQ panel that duplicates other verdicts.
- Upgrade: Convert into a meta-evidence audit over independent scored hypotheses, with anomaly weights computed from the verdict inventory.
- Scoreboard rule: Do not score as a direct policy verdict; use it to explain confidence and anomaly handling in the policy browser.
- Candidate data: scoreboard verdict inventory, evidence quality weights, country/period coverage metadata
- Local availability: Use the conversion audit, scoreboard audit, and result-card metadata already generated in engine/audits and engine/runs.

### 5. `CBDC_design_privacy_tradeoff`

- Verdict: PARTIAL — coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `active_labour_market_policy_conditionality_works`

- Verdict: PARTIAL — coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `agricultural_export_ban_price_instability`

- Verdict: PARTIAL — coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `agricultural_trade_liberalisation_food_security`

- Verdict: PARTIAL — coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `apprenticeship_employer_chamber_quality`

- Verdict: PARTIAL — coef=+9.405e-17, p=1.03e-08; effect magnitude effectively zero
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `campaign_favoritism_subsidy_allocation`

- Verdict: SUPPORTED — coef=-0.3453 (sign matches claim -), p=0.0312
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `crony_capitalism_not_market_freedom`

- Verdict: SUPPORTED — coef=+0.205 (sign matches claim +), p=0.0329
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `intervention_intensity_qol_volatility_1970_2024`

- Verdict: SUPPORTED — coef=-0.3453 (sign matches claim -), p=0.0312
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `intervention_reversal_qol_loss_1980_2024`

- Verdict: SUPPORTED — coef=-0.3453 (sign matches claim -), p=0.0312
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `labor_reform_real_wage_growth`

- Verdict: SUPPORTED — coef=+3078 (sign matches claim +), p=0.00422
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `licensing_discretion_bribery`

- Verdict: SUPPORTED — coef=+0.205 (sign matches claim +), p=0.0329
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `market_institution_duration_qol_persistence`

- Verdict: REFUTED — coef=+3078 (sign opposite claim -), p=0.00422
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `market_reform_inflation_adjusted_wages`

- Verdict: REFUTED — coef=+3078 (sign opposite claim -), p=0.00422
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `price_signal_integrity_qol_panel`

- Verdict: REFUTED — coef=+3078 (sign opposite claim -), p=0.00422
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.

### 5. `procurement_competition_corruption`

- Verdict: SUPPORTED — coef=+0.205 (sign matches claim +), p=0.0329
- Decision: review_duplicate_context
- Problem: Held because this verdict shares a broad-panel fingerprint with other hypotheses.
- Upgrade: Inspect claim wording and replace generic proxy inputs with claim-specific treatment and outcome data.
- Scoreboard rule: Keep out of scoreboard until the duplicate evidence path is resolved.
