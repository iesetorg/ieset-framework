# Local Panel Sprint Results - 2026-05-03

## Methodology Gate

- Pre-registration commit: `b0b51ca`
- Runner commit at estimation: `b0b51ca84320b159df4eae8d56298a4f63366b9f`
- Estimation was run only after the 48 specs and steelmen were committed.
- No school-scoreboard mappings were asserted in this wave.
- Each run directory includes `diagnostics.json`, `result_card.md`, and `replication.py`.

## Counts

- SUPPORTED: 11
- REFUTED: 2
- PARTIAL: 35

## FDR q<=0.10

- SUPPORTED: 6
- REFUTED: 1

## FDR q<=0.05

- SUPPORTED: 6
- REFUTED: 1

## By Mechanism

- broad_money_growth: PARTIAL=4
- capital_account_openness: PARTIAL=4
- control_corruption: PARTIAL=3, REFUTED=1
- fiscal_balance: PARTIAL=1, SUPPORTED=3
- government_effectiveness: PARTIAL=4
- government_spending: SUPPORTED=4
- inflation_rate: PARTIAL=2, REFUTED=1, SUPPORTED=1
- public_debt: PARTIAL=3, SUPPORTED=1
- regulatory_quality: PARTIAL=4
- rule_of_law: PARTIAL=4
- tax_revenue: PARTIAL=3, SUPPORTED=1
- trade_openness: PARTIAL=3, SUPPORTED=1

## Results

- `local_panel_sprint_rule_of_law_gdp_pc_growth_20260503`: PARTIAL | coef=-0.2617 | p=0.6942 | q=0.8339 | n=1297 | countries=52
- `local_panel_sprint_rule_of_law_investment_share_20260503`: PARTIAL | coef=+0.02398 | p=0.9852 | q=0.9852 | n=1295 | countries=52
- `local_panel_sprint_rule_of_law_private_credit_depth_20260503`: PARTIAL | coef=-2.286 | p=0.75 | q=0.8552 | n=1133 | countries=52
- `local_panel_sprint_rule_of_law_high_tech_exports_20260503`: PARTIAL | coef=+0.8956 | p=0.5433 | q=0.7671 | n=845 | countries=52
- `local_panel_sprint_regulatory_quality_gdp_pc_growth_20260503`: PARTIAL | coef=+0.8238 | p=0.1017 | q=0.3488 | n=1297 | countries=52
- `local_panel_sprint_regulatory_quality_investment_share_20260503`: PARTIAL | coef=+1.557 | p=0.1203 | q=0.3672 | n=1295 | countries=52
- `local_panel_sprint_regulatory_quality_employment_rate_20260503`: PARTIAL | coef=+1.496 | p=0.2269 | q=0.5446 | n=1297 | countries=52
- `local_panel_sprint_regulatory_quality_manufacturing_share_20260503`: PARTIAL | coef=-0.6859 | p=0.2432 | q=0.556 | n=1285 | countries=52
- `local_panel_sprint_control_corruption_gdp_pc_growth_20260503`: PARTIAL | coef=+0.9996 | p=0.1224 | q=0.3672 | n=1297 | countries=52
- `local_panel_sprint_control_corruption_investment_share_20260503`: PARTIAL | coef=+0.3011 | p=0.7661 | q=0.8552 | n=1295 | countries=52
- `local_panel_sprint_control_corruption_private_credit_depth_20260503`: REFUTED | coef=-13.37 | p=0.08829 | q=0.326 | n=1133 | countries=52
- `local_panel_sprint_control_corruption_high_tech_exports_20260503`: PARTIAL | coef=+1.143 | p=0.3673 | q=0.7091 | n=845 | countries=52
- `local_panel_sprint_government_effectiveness_gdp_pc_growth_20260503`: PARTIAL | coef=+0.6925 | p=0.1463 | q=0.3901 | n=1297 | countries=52
- `local_panel_sprint_government_effectiveness_investment_share_20260503`: PARTIAL | coef=+0.1507 | p=0.9037 | q=0.943 | n=1295 | countries=52
- `local_panel_sprint_government_effectiveness_gross_savings_share_20260503`: PARTIAL | coef=+0.8637 | p=0.4355 | q=0.7466 | n=1279 | countries=52
- `local_panel_sprint_government_effectiveness_manufacturing_share_20260503`: PARTIAL | coef=-0.5145 | p=0.4901 | q=0.7475 | n=1285 | countries=52
- `local_panel_sprint_capital_account_openness_gdp_pc_growth_20260503`: PARTIAL | coef=+0.2327 | p=0.7296 | q=0.8542 | n=1453 | countries=52
- `local_panel_sprint_capital_account_openness_investment_share_20260503`: PARTIAL | coef=-2.118 | p=0.1996 | q=0.5041 | n=1449 | countries=52
- `local_panel_sprint_capital_account_openness_fdi_inflows_share_20260503`: PARTIAL | coef=+0.8422 | p=0.4139 | q=0.7359 | n=1453 | countries=52
- `local_panel_sprint_capital_account_openness_high_tech_exports_20260503`: PARTIAL | coef=-0.5356 | p=0.8664 | q=0.9242 | n=845 | countries=52
- `local_panel_sprint_trade_openness_gdp_pc_growth_20260503`: PARTIAL | coef=+0.008016 | p=0.3226 | q=0.6733 | n=1453 | countries=52
- `local_panel_sprint_trade_openness_investment_share_20260503`: PARTIAL | coef=-0.02374 | p=0.281 | q=0.613 | n=1449 | countries=52
- `local_panel_sprint_trade_openness_manufacturing_share_20260503`: SUPPORTED | coef=+0.06068 | p=1.876e-07 | q=4.503e-06 | n=1436 | countries=52; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_trade_openness_high_tech_exports_20260503`: PARTIAL | coef=+0.01609 | p=0.5008 | q=0.7475 | n=845 | countries=52
- `local_panel_sprint_inflation_rate_gdp_pc_growth_20260503`: SUPPORTED | coef=-0.06927 | p=0.002379 | q=0.01904 | n=1431 | countries=52; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_inflation_rate_investment_share_20260503`: PARTIAL | coef=-0.00231 | p=0.9437 | q=0.9638 | n=1427 | countries=52
- `local_panel_sprint_inflation_rate_employment_rate_20260503`: REFUTED | coef=+0.0595 | p=0.004258 | q=0.02919 | n=1431 | countries=52; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_inflation_rate_private_credit_depth_20260503`: PARTIAL | coef=+0.116 | p=0.5045 | q=0.7475 | n=1208 | countries=52
- `local_panel_sprint_broad_money_growth_gdp_pc_growth_20260503`: PARTIAL | coef=-0.004635 | p=0.6659 | q=0.8339 | n=973 | countries=36
- `local_panel_sprint_broad_money_growth_investment_share_20260503`: PARTIAL | coef=+0.00642 | p=0.5762 | q=0.7902 | n=969 | countries=36
- `local_panel_sprint_broad_money_growth_gross_savings_share_20260503`: PARTIAL | coef=+0.005221 | p=0.5139 | q=0.7475 | n=969 | countries=36
- `local_panel_sprint_broad_money_growth_private_credit_depth_20260503`: PARTIAL | coef=-0.0328 | p=0.6605 | q=0.8339 | n=887 | countries=36
- `local_panel_sprint_government_spending_gdp_pc_growth_20260503`: SUPPORTED | coef=-0.2569 | p=1.517e-09 | q=7.283e-08 | n=1282 | countries=51; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_government_spending_investment_share_20260503`: SUPPORTED | coef=-0.14 | p=0.05885 | q=0.2568 | n=1282 | countries=51
- `local_panel_sprint_government_spending_gross_savings_share_20260503`: SUPPORTED | coef=-0.2576 | p=0.0008053 | q=0.007731 | n=1257 | countries=51; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_government_spending_manufacturing_share_20260503`: SUPPORTED | coef=-0.1159 | p=0.05536 | q=0.2568 | n=1276 | countries=51
- `local_panel_sprint_tax_revenue_gdp_pc_growth_20260503`: PARTIAL | coef=+0.058 | p=0.3938 | q=0.727 | n=1313 | countries=51
- `local_panel_sprint_tax_revenue_investment_share_20260503`: PARTIAL | coef=+0.195 | p=0.3693 | q=0.7091 | n=1309 | countries=51
- `local_panel_sprint_tax_revenue_employment_rate_20260503`: PARTIAL | coef=+0.06295 | p=0.622 | q=0.8294 | n=1313 | countries=51
- `local_panel_sprint_tax_revenue_manufacturing_share_20260503`: SUPPORTED | coef=-0.2338 | p=0.07013 | q=0.2805 | n=1302 | countries=51
- `local_panel_sprint_public_debt_gdp_pc_growth_20260503`: PARTIAL | coef=-0.008717 | p=0.4653 | q=0.7475 | n=501 | countries=27
- `local_panel_sprint_public_debt_investment_share_20260503`: SUPPORTED | coef=-0.05749 | p=0.03115 | q=0.1772 | n=497 | countries=27
- `local_panel_sprint_public_debt_gross_savings_share_20260503`: PARTIAL | coef=-0.008112 | p=0.6949 | q=0.8339 | n=501 | countries=27
- `local_panel_sprint_public_debt_private_credit_depth_20260503`: PARTIAL | coef=-0.04158 | p=0.8542 | q=0.9242 | n=417 | countries=25
- `local_panel_sprint_fiscal_balance_gdp_pc_growth_20260503`: SUPPORTED | coef=+0.2655 | p=2.858e-07 | q=4.574e-06 | n=1250 | countries=50; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_fiscal_balance_investment_share_20260503`: PARTIAL | coef=+0.138 | p=0.1364 | q=0.3851 | n=1250 | countries=50
- `local_panel_sprint_fiscal_balance_gross_savings_share_20260503`: SUPPORTED | coef=+0.3554 | p=0.0001353 | q=0.001623 | n=1225 | countries=50; FDR q<=0.10; FDR q<=0.05
- `local_panel_sprint_fiscal_balance_employment_rate_20260503`: SUPPORTED | coef=+0.1074 | p=0.03322 | q=0.1772 | n=1250 | countries=50
