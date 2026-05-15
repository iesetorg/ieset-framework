# Scoreboard Easy-Win Mapping Patch Plan

Date: 2026-05-15
Source audit: `engine/audits/scoreboard_safe_graduation_opportunities_2026-05-15.md`
Scope: audit and patch plan only; no position or hypothesis YAML edited.

## Recommendation

Smallest safe mapping batch: map only `bis_credit_gap_current_account_twin_deficit_risk`, with two aligned reciprocal mappings:

- `positions/post_keynesian.yaml`
- `positions/marxian.yaml`

Reason: the target files already have adjacent financial-instability / credit-boom-bust claims, the hypothesis wording is narrow, the result is decisive enough for low-weight associational graduation, and reciprocal `covers_claims` can be added without polarity ambiguity.

Do not insert these claims in the thematic middle of the files unless all downstream `claim_index` references are recalculated. Existing hypothesis-side reciprocal links use positional `claim_index`, so the safe target is append-only at the end of each `falsifiable_specific_claims` list, immediately before the root-level `notes:` / `scope_decisions:` blocks.

## Exact Patch Targets

### `positions/post_keynesian.yaml`

Insert immediately before root-level `notes:` at current line 3341. Existing final claim index is 135, so the appended claim should be `claim_index: 136`.

```yaml
- claim: 'Post-Keynesian economics predicts this financial-instability claim should hold: In BIS/WDI country panels from 1970-2025, credit-gap stress predicts larger two-year unemployment increases when current accounts are in deficit, after country and year fixed effects. The mechanism is Minskyan external-balance fragility: domestic credit booms become more employment-damaging when external financing constraints tighten.'
  linked_hypothesis_id: bis_credit_gap_current_account_twin_deficit_risk
  school_prediction: supported
  claim_polarity: aligned
  empirical_status: supported
  scope:
    period: [1970, 2025]
    countries: [GLOBAL]
    outcome_dim: [financial_crisis, employment_labour, capital_flows]
    policy_family: [monetary_policy, exchange_rate_regime]
    treatment_tags: [credit_gap_x_current_account_deficit, credit_gap, current_account_deficit]
  notes: '2026-05-15 scoreboard easy-win audit: append-only low-q associational mapping; reciprocal hypothesis link should be added before scoreboard recompute.'
```

Add to `hypotheses/monetary/bis_credit_gap_current_account_twin_deficit_risk.yaml`:

```yaml
covers_claims:
- position_id: post_keynesian
  claim_index: 136
  polarity: aligned
  school_prediction: supported
  confidence: medium
  notes: 2026-05-15 scoreboard easy-win audit; appended to avoid shifting existing claim_index references.
```

### `positions/marxian.yaml`

Insert immediately before root-level `scope_decisions:` at current line 3163. Existing final claim index is 138, so the appended claim should be `claim_index: 139`.

```yaml
- claim: 'Marxian political economy predicts this financial-instability claim should hold: In BIS/WDI country panels from 1970-2025, credit-gap stress predicts larger two-year unemployment increases when current accounts are in deficit, after country and year fixed effects. The mechanism is financialised accumulation under external dependence: credit expansions are more crisis-prone and labour-damaging where current-account deficits expose economies to financing constraints.'
  linked_hypothesis_id: bis_credit_gap_current_account_twin_deficit_risk
  school_prediction: supported
  claim_polarity: aligned
  empirical_status: supported
  scope:
    period: [1970, 2025]
    countries: [GLOBAL]
    outcome_dim: [financial_crisis, employment_labour, capital_flows]
    policy_family: [monetary_policy, exchange_rate_regime]
    treatment_tags: [credit_gap_x_current_account_deficit, credit_gap, current_account_deficit]
  notes: '2026-05-15 scoreboard easy-win audit: append-only low-q associational mapping; reciprocal hypothesis link should be added before scoreboard recompute.'
```

If the Post-Keynesian mapping above is also applied, extend the same `covers_claims` list in `hypotheses/monetary/bis_credit_gap_current_account_twin_deficit_risk.yaml`:

```yaml
- position_id: marxian
  claim_index: 139
  polarity: aligned
  school_prediction: supported
  confidence: medium
  notes: 2026-05-15 scoreboard easy-win audit; appended to avoid shifting existing claim_index references.
```

## Secondary Candidates

### `eurostat_electricity_price_inflation_pass_through`

Recommendation: hold for author review rather than include in the smallest batch.

Reason: `positions/new_keynesian.yaml` has an adjacent UK energy-price inflation claim at line 1137 and could accept a narrow EU short-panel pass-through claim, but `positions/post_keynesian.yaml` has no equally clean cost-push insertion point near its current end, and Chicago mapping would require careful short-run wording to avoid overstating monetarist persistence. This is likely mappable, but it is not the smallest no-ambiguity batch.

Safe later wording for New Keynesian only:

> New Keynesian economics predicts this cost-shock transmission claim should hold: industrial electricity-price inflation passes through to headline CPI inflation in short European country panels, consistent with input-cost shocks entering the short-run inflation process.

### `oecd_socx_public_social_spending_employment_tradeoff`

Recommendation: hold.

Reason: the result is strong, but the target files already contain broader government-expenditure employment claims. Mapping SOCX public social spending directly onto generic government spending risks double-counting a narrower welfare-state treatment as the same fiscal-size mechanism. A safe mapping should either create a distinct welfare-spending claim in market-liberal files or deliberately add inverted welfare-compatibility claims to left files; that is larger than an easy-win batch.

### `bls_minimum_wage_bite_low_tail_threshold_panel`

Recommendation: hold.

Reason: there are existing high-bite minimum-wage claims in `positions/classical_liberal.yaml`, `positions/chicago_monetarism.yaml`, and `positions/austrian.yaml`, but the recent minimum-wage bundle has conflicting sibling results and this run is near threshold (`p=0.0840`). A narrow low-q mapping may be possible later, but it should wait for bundle QA so the scoreboard does not over-read a single threshold panel.

## Verification If Applied

If the YAML mappings are applied later:

1. Run the repository's link-reciprocity checker.
2. Confirm `bis_credit_gap_current_account_twin_deficit_risk` appears in exactly two position files unless a broader batch is intentionally chosen.
3. Confirm no existing `covers_claims.claim_index` entries changed meaning due to insertion order.
