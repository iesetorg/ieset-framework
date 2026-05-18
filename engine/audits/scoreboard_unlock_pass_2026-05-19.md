# Scoreboard Unlock Pass

Generated: 2026-05-19

## Scope

This pass followed the May 19 mapping-gate audit by targeting the real bottleneck: decisive unmapped runs that were blocked by either missing reciprocal claim links or missing evidence packets.

Known unrelated loose files were not touched:

- `web/app/scoreboard/page.tsx`
- `data/manifests/fetch_run_2026-05-17T231721Z.yaml`
- `data/manifests/fetch_run_2026-05-17T231736Z.yaml`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`

## Scoreboard Mappings Applied

Five direct reciprocal mappings were added.

| hypothesis | positions mapped | rationale |
| --- | --- | --- |
| `eurostat_electricity_price_inflation_pass_through` | `new_keynesian`, `post_keynesian` | Direct short-panel cost-shock / cost-push inflation claim; supported verdict; complete evidence packet already existed. |
| `oecd_socx_public_social_spending_employment_tradeoff` | `classical_liberal`, `chicago_monetarism`, `austrian` | Direct OECD SOCX employment-rate tradeoff; supported verdict; complete enough for low-q associational mapping. |

Mapping swing relative to `scoreboard_prediction_outcome_audit_2026-05-19_after_swarm_cleanup`:

| school | q-net delta | raw-net delta | tested delta |
| --- | ---: | ---: | ---: |
| `austrian` | +0.5 | +1.0 | +1 |
| `chicago_monetarism` | +0.5 | +1.0 | +1 |
| `classical_liberal` | +0.5 | +1.0 | +1 |
| `new_keynesian` | +0.5 | +1.0 | +1 |
| `post_keynesian` | +0.5 | +1.0 | +1 |

Fresh recompute:

- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-19_after_scoreboard_unlock_pass.json`
- `engine/audits/scoreboard_prediction_outcome_audit_2026-05-19_after_scoreboard_unlock_pass.md`

Public claim links moved from 2,309 to 2,314.

## Evidence Packet Backfill

Generated evidence packets for 73 decisive, unmapped, non-Heritage runs that had no packet at the start of this pass.

| packet grade after backfill | count | scoreboard meaning |
| --- | ---: | --- |
| `reproducible_hash_verified` | 13 | Strongest next conversion candidates after duplicate/design review. |
| `partial_provenance` | 17 | Potentially mappable only if the claim is direct and not duplicative. |
| `no_input_vintages_recorded` | 43 | Packet exists, but still not scoreboard-safe until manifests/vintages are repaired. |

The backfill changed the near-term conversion pool: there are now 69 decisive, unmapped, non-Heritage runs with either `reproducible_hash_verified` or `partial_provenance` evidence packets.

## Next Conversion Queue

The 69-run pool should not be mapped as one batch. It clusters into very different evidence families.

### Best Direct Candidates

These are the next candidates to inspect for narrow reciprocal links.

- `wdi_business_entry_rule_of_law_growth_panel`
- `financial_boe_independence_1997_macroprudential_2013`
- `trade_lib_bangladesh_apparel_eu_eba_2008`
- `trade_lib_south_africa_sadc_trade`
- `trade_lib_colombia_us_fta_2012`
- `trade_lib_egypt_fta_cascade`
- `trade_lib_argentina_mercosur_industrial_effect`
- `japan_zero_growth_basic_wellbeing_intact`
- `monetary_finance_zlb_no_inflation`
- `bis_credit_gap_current_account_interaction_panel_1970_2025`
- `bis_dsr_house_price_boom_reversal_panel_1999_2025`

### Hold As Clustered Evidence

These may be useful, but they should be consolidated or capped before scoreboard conversion.

- Banking-crisis canonical cases: many supported case studies share the same financial-instability mechanism. Mapping each one independently would overweight a single thesis. Convert through a capped crisis-cluster mapping plan or a meta-hypothesis.
- Singapore/UAE canonical development cases: useful, but they mix market openness, state capacity, public ownership, and resource/state-capitalist mechanisms. Mapping them mechanically would distort the developmentalism split.
- WGI proxy cluster: `procurement_competition_corruption`, `licensing_discretion_bribery`, `rule_bound_regulation_business_trust`, `crony_capitalism_not_market_freedom`, `market_governance_qol_broad_scope`, `frontier_qol_market_institutions_1990_2024`. Keep out until direct procurement/licensing/business-trust/outcome data are used or the cluster is scored as one meta-screen.

### Provenance Repair Queue

The 43 `no_input_vintages_recorded` packets are now visible but still not eligible for scoreboard conversion. The next repair is to regenerate or reconstruct manifests with explicit vintage inputs, then rerun packet generation.

High-value examples:

- `campaign_favoritism_subsidy_allocation`
- `intervention_reversal_qol_loss_1980_2024`
- `intervention_intensity_qol_volatility_1970_2024`
- `price_signal_integrity_qol_panel`
- `tax_simplicity_disposable_income_growth`
- `occupational_licensing_income_mobility`

## Validation

- `python3 scripts/validate_link_reciprocity.py --summary`: 0 errors, 0 warnings.
- `python3 scripts/validate_scope_alignment.py`: 0 errors, 10 warnings.
- Reciprocal claim-index spot check passed for all five new mappings.
