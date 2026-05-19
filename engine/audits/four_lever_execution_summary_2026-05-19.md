# Four-Lever Execution Summary — 2026-05-19

Executed four unlock levers in order: provenance, scoreboard conversion,
partial-result interpretation, and data-source bridges.

## 1. Evidence Provenance Backfill

Generated evidence packets for 30 high-impact mapped runs with weak or absent
provenance indexing.

- 9 moved to `reproducible_hash_verified`
- 15 moved to `partial_provenance`
- 6 remain `no_input_vintages_recorded`

Highest-value verified upgrades included:

- `labour_market_flexibility_unemployment_duration`
- `german_manufacturing_va_decline_2017_2024`
- the four `market_order_government_spending_*` panels
- `fiscal_consolidation_credibility_growth`
- `oecd_public_transfers_poverty_reduction_panel`
- `oecd_market_to_disposable_gini_compression_panel`

## 2. Clean Scoreboard Conversion

Added reciprocal scoreboard links only where the hypothesis-to-school mechanism
was tight:

- `abct_credit_boom_predicts_capital_misallocation_oecd`
- `austrian_monetary_expansion_asset_bubble_not_cpi_panel`
- `korea_post_chaebol_liberalisation_frontier_growth`
- `uae_freezone_institutional_quality_wgi_1996_2024`
- `cuba_health_outcomes_vs_latam_peers`

These created new mappings across Austrian, classical liberal, Chicago monetarist,
developmentalist, institutionalist, ordoliberal, Marxist-Leninist, democratic
socialist, and social-democratic schools.

## 3. Partial-Result Interpretation

Converted only one `PARTIAL` verdict:

- `capital_gains_tax_cut_investment_response_panel`
  - investment leg supported;
  - business-entry leg not supported;
  - mapped as partial evidence for `classical_liberal` and `chicago_monetarism`.

Created the triage queue in
`engine/audits/partial_result_interpretation_queue_2026-05-19.md` so ambiguous
partials are split or held rather than converted carelessly.

## 4. Data-Source Bridges

Patched the runnability resolver and publisher aliases.

Runnability movement:

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| READY | 1474 | 1511 | +37 |
| NEEDS_DATA | 137 | 101 | -36 |
| NEEDS_TEMPLATE | 1 | 0 | -1 |
| LEGACY_SCHEMA | 0 | 0 | 0 |

Details are in `engine/audits/data_source_bridge_unlocks_2026-05-19.md`.

## Scoreboard Movement

Compared with `scoreboard_prediction_outcome_audit_2026-05-19_after_deeper_unlock_pass`:

| School | Tested delta | Net delta | Adjusted net delta |
|---|---:|---:|---:|
| austrian | +2 | +0.0 | +0.00 |
| chicago_monetarism | +2 | -0.5 | -0.25 |
| classical_liberal | +3 | +0.5 | +0.00 |
| democratic_socialist | +1 | +1.0 | +0.50 |
| developmentalism | +2 | +2.0 | +0.75 |
| institutionalism | +1 | +1.0 | +0.25 |
| marxist_leninist | +1 | +1.0 | +0.50 |
| ordoliberal | +1 | +1.0 | +0.25 |
| social_democratic | +1 | +1.0 | +0.50 |

Interpretation: the pass added breadth and stronger provenance rather than a
large directional swing. Austrian got one support and one refutation. The largest
positive movement was developmentalism, driven by the Korea phase-comparison
refuting the strong liberalisation-outperformance claim and the UAE state-capacity
case.

## Validation

- Targeted touched-file schema validation: OK
- `validate_scope_alignment.py`: 2514 pass, 0 errors, 10 warnings
- `validate_link_reciprocity.py --summary`: 2524 position links, 2524 hypothesis coverages, 0 errors, 0 warnings
- Full `validate_specs.py` still has pre-existing corpus-wide failures; this pass
  did not add touched-file schema failures.
