# Fiscal/tax swarm C audit - 2026-05-18

Worker C scope: fiscal/tax/public-finance hypotheses only. No scoreboard, position, fetch-manifest, or daily-rate-limited backfill files were edited.

## Selection rule

Selected 12 `hypotheses/fiscal` runs that already had non-pending verdicts, result cards, and replication wrappers, but lacked exact run-level manifests. This graduates preflight-ready artifacts without timestamp-only reruns.

## Graduated artifacts

| hypothesis | verdict | manifest | local vintage count | blockers |
|---|---:|---|---:|---|
| `market_order_fiscal_balance_gross_savings_share_panel` | SUPPORTED | `engine/runs/market_order_fiscal_balance_gross_savings_share_panel/manifest.yaml` | 5 | none |
| `market_order_fiscal_balance_private_credit_depth_panel` | REFUTED | `engine/runs/market_order_fiscal_balance_private_credit_depth_panel/manifest.yaml` | 5 | none |
| `market_order_fiscal_balance_private_investment_share_panel` | SUPPORTED | `engine/runs/market_order_fiscal_balance_private_investment_share_panel/manifest.yaml` | 5 | none |
| `market_order_government_spending_employment_rate_panel` | SUPPORTED | `engine/runs/market_order_government_spending_employment_rate_panel/manifest.yaml` | 5 | none |
| `market_order_government_spending_gdp_pc_growth_panel` | SUPPORTED | `engine/runs/market_order_government_spending_gdp_pc_growth_panel/manifest.yaml` | 5 | none |
| `market_order_government_spending_investment_share_panel` | SUPPORTED | `engine/runs/market_order_government_spending_investment_share_panel/manifest.yaml` | 5 | none |
| `market_order_government_spending_private_credit_depth_panel` | REFUTED | `engine/runs/market_order_government_spending_private_credit_depth_panel/manifest.yaml` | 5 | none |
| `market_order_public_debt_gross_savings_share_panel` | PARTIAL | `engine/runs/market_order_public_debt_gross_savings_share_panel/manifest.yaml` | 5 | none |
| `market_order_public_debt_private_credit_depth_panel` | PARTIAL | `engine/runs/market_order_public_debt_private_credit_depth_panel/manifest.yaml` | 5 | none |
| `market_order_public_debt_private_investment_share_panel` | SUPPORTED | `engine/runs/market_order_public_debt_private_investment_share_panel/manifest.yaml` | 5 | none |
| `market_order_tax_burden_employment_rate_panel` | PARTIAL | `engine/runs/market_order_tax_burden_employment_rate_panel/manifest.yaml` | 5 | none |
| `market_order_tax_burden_gdp_pc_growth_panel` | PARTIAL | `engine/runs/market_order_tax_burden_gdp_pc_growth_panel/manifest.yaml` | 5 | none |

## Verification completed

- `python3 -m py_compile` passed for all 12 existing replication wrappers.
- Manifest validation passed: all new YAML files parse, hypothesis/spec/card/diagnostics references exist, and every recorded local vintage path matches its recorded SHA-256.
- ASCII scan passed for the new audit plus all 12 new manifests.
- No wrapper was newly created in this lane; existing wrappers are preserved to avoid run timestamp churn.

## Notes

- The manifests record the current local vintage files resolved by `scripts/run_panel_fe.py` for each variable listed in existing diagnostics.
- Existing verdicts were not changed. Result cards and diagnostics were not rerun or rewritten.
- Blockers for this lane: none for the 12 graduated artifacts. Repair-heavy candidates such as `wealth_tax_capital_flight_revenue_yield_gap` remain blocked on country/event source panels and were not touched.
