# Scoreboard Deeper Unlock Pass

Date: 2026-05-19

## Purpose

This pass maps the next safest direct-policy subset from the verified decisive
unmapped inventory into school claims. The goal is to move the scoreboard with
high-traceability links, not to bulk-convert every adjacent result.

## Guardrails

- No benchmark-control mappings were added.
- No Fed operational facts were mapped, because they are descriptive plumbing rather
  than school-level policy predictions.
- Duplicate financial-crisis variants were held unless the hypothesis directly
  tested a school mechanism.
- Mixed trade cases were only mapped when the school prediction was narrow enough
  to score cleanly.

## Mapped Hypotheses

| hypothesis | verdict | evidence | added school links | q-net direction |
| --- | --- | --- | ---: | --- |
| `wdi_business_entry_rule_of_law_growth_panel` | supported | associational | 3 | +0.5 each to classical liberal, ordoliberal, institutionalism |
| `financial_boe_independence_1997_macroprudential_2013` | supported | associational | 3 | +0.5 each to Chicago monetarism, New Keynesian, institutionalism |
| `monetary_finance_zlb_no_inflation` | refuted | associational | 1 | -0.5 to MMT |
| `household_debt_minsky_cycle_2008` | refuted | associational | 2 | -0.5 each to Post-Keynesian and Marxian |
| `trade_lib_bangladesh_apparel_eu_eba_2008` | supported | descriptive | 3 | +0.25 each to classical liberal, Chicago monetarism, developmentalism |
| `trade_lib_argentina_mercosur_industrial_effect` | supported | descriptive | 2 | +0.25 each to classical liberal and Chicago monetarism |

Total new reciprocal claim links: 14.

## Scoreboard Movement

Compared with `scoreboard_prediction_outcome_audit_2026-05-19_after_scoreboard_unlock_pass`.

| school | q-net before | q-net after | delta | interpretation |
| --- | ---: | ---: | ---: | --- |
| `chicago_monetarism` | 23.6 | 24.6 | +1.0 | BoE institutions plus two trade cases |
| `classical_liberal` | 20.6 | 21.6 | +1.0 | rule-of-law entry plus two trade cases |
| `institutionalism` | 3.6 | 4.6 | +1.0 | rule-of-law entry plus BoE institutional architecture |
| `ordoliberal` | 20.1 | 20.6 | +0.5 | rule-bound entrepreneurship complement |
| `new_keynesian` | 4.8 | 5.2 | +0.5 | central-bank institution stability |
| `developmentalism` | 14.0 | 14.2 | +0.25 | Bangladesh apparel upgrading |
| `mmt` | -3.0 | -3.5 | -0.5 | slack-regime monetary-finance CPI gate refuted |
| `post_keynesian` | -1.4 | -1.9 | -0.5 | household-credit Minsky prediction refuted |
| `marxian` | -1.8 | -2.2 | -0.5 | household-credit financialisation prediction refuted |

The rounded audit table displays one decimal place, so the descriptive-link
increments appear as +0.2 in some rows even though the scorer applies +0.25.

## Current Ranked Read

The main ordering after this pass is unchanged, but the top market-institution
cluster widened slightly:

- `chicago_monetarism`: q-net 24.6
- `classical_liberal`: q-net 21.6
- `ordoliberal`: q-net 20.6
- `austrian`: q-net 17.9
- `developmentalism`: q-net 14.2

The center-left and socialist cluster remains mostly inside the no-call band,
with `degrowth` still the only clearly negative signal in the ranked table.

## Held For Later

- `financial_fed_dot_plot_realised_path_2012_2024` and
  `financial_fed_reverse_repo_facility_usage_2021_2024`: operational facts, not
  direct school predictions.
- `bis_credit_gap_current_account_interaction_panel_1970_2025`: useful, but too
  close to an already mapped BIS twin-deficit claim.
- `bis_dsr_house_price_boom_reversal_panel_1999_2025`: refuted_or_weak gate, not
  clean enough for the next lever.
- `trade_lib_colombia_us_fta_2012`, `trade_lib_south_africa_sadc_trade`, and
  `trade_lib_egypt_fta_cascade`: mixed institutional-capacity trade cases that
  need narrower claim wording before scoreboard conversion.

## Validation

- `python3 scripts/validate_link_reciprocity.py --summary`: 2510 position-side
  links, 2510 hypothesis-side coverages, 0 errors, 0 warnings.
- `python3 scripts/validate_scope_alignment.py`: 2500 pass, 0 errors, 10 warnings
  from pre-existing missing-scope rows.
- `python3 scripts/audit_scoreboard_outcomes.py --out engine/audits/scoreboard_prediction_outcome_audit_2026-05-19_after_deeper_unlock_pass`:
  wrote fresh JSON and Markdown audit outputs.
- `git diff --check`: clean.

`python3 scripts/validate_specs.py` still fails on unrelated pre-existing backlog
schema issues, so it is not used as the acceptance gate for this narrow mapping pass.
