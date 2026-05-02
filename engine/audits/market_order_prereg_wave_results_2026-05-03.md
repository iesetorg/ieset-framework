# Market-Order Pre-Registration Wave Results - 2026-05-03

- Pre-registration commit: `730d173`
- Runner interaction-detector fix commit: `2906de0`

## Raw Verdict Counts

- PARTIAL: 24
- SUPPORTED: 5
- REFUTED: 3

## FDR q<=0.10 Counts

- SUPPORTED: 4
- REFUTED: 2

## Mechanism Mix

- control_corruption: {'PARTIAL': 3, 'REFUTED': 1}
- economic_freedom: {'PARTIAL': 4}
- government_spending: {'SUPPORTED': 3, 'REFUTED': 1}
- regulatory_quality: {'SUPPORTED': 1, 'PARTIAL': 3}
- rule_of_law: {'PARTIAL': 4}
- sound_money: {'PARTIAL': 2, 'SUPPORTED': 1, 'REFUTED': 1}
- tax_burden: {'PARTIAL': 4}
- trade_openness: {'PARTIAL': 4}

## Results

- `market_order_rule_of_law_investment_share_panel` | PARTIAL | coef=-0.7793 | p=0.5575 | q=0.6861 | n=1297
- `market_order_rule_of_law_private_credit_depth_panel` | PARTIAL | coef=-2.286 | p=0.75 | q=0.8 | n=1133
- `market_order_rule_of_law_gdp_pc_growth_panel` | PARTIAL | coef=-0.2617 | p=0.6942 | q=0.766 | n=1297
- `market_order_rule_of_law_high_tech_exports_panel` | PARTIAL | coef=+0.8956 | p=0.5433 | q=0.6861 | n=845
- `market_order_regulatory_quality_investment_share_panel` | SUPPORTED | coef=+1.647 | p=0.09215 | q=0.3617 | n=1297
- `market_order_regulatory_quality_employment_rate_panel` | PARTIAL | coef=+1.496 | p=0.2269 | q=0.5729 | n=1297
- `market_order_regulatory_quality_high_tech_exports_panel` | PARTIAL | coef=+2.33 | p=0.1899 | q=0.5524 | n=845
- `market_order_regulatory_quality_gdp_pc_growth_panel` | PARTIAL | coef=+0.8238 | p=0.1017 | q=0.3617 | n=1297
- `market_order_control_corruption_investment_share_panel` | PARTIAL | coef=-0.01768 | p=0.9865 | q=0.9865 | n=1297
- `market_order_control_corruption_private_credit_depth_panel` | REFUTED | coef=-13.37 | p=0.08829 | q=0.3617 | n=1133
- `market_order_control_corruption_gdp_pc_growth_panel` | PARTIAL | coef=+0.9996 | p=0.1224 | q=0.3917 | n=1297
- `market_order_control_corruption_high_tech_exports_panel` | PARTIAL | coef=+1.143 | p=0.3673 | q=0.653 | n=845
- `market_order_economic_freedom_investment_share_panel` | PARTIAL | coef=-0.7318 | p=0.3494 | q=0.653 | n=1245
- `market_order_economic_freedom_gdp_pc_growth_panel` | PARTIAL | coef=+0.6954 | p=0.2328 | q=0.5729 | n=1245
- `market_order_economic_freedom_employment_rate_panel` | PARTIAL | coef=+0.519 | p=0.5866 | q=0.6952 | n=1245
- `market_order_economic_freedom_high_tech_exports_panel` | PARTIAL | coef=-0.3101 | p=0.8412 | q=0.8683 | n=845
- `market_order_sound_money_investment_share_panel` | PARTIAL | coef=+0.02161 | p=0.5138 | q=0.685 | n=1431
- `market_order_sound_money_gdp_pc_growth_panel` | SUPPORTED | coef=-0.06927 | p=0.002379 | q=0.02538 | n=1431
- `market_order_sound_money_private_credit_depth_panel` | PARTIAL | coef=+0.116 | p=0.5045 | q=0.685 | n=1208
- `market_order_sound_money_employment_rate_panel` | REFUTED | coef=+0.0595 | p=0.004258 | q=0.03303 | n=1431
- `market_order_government_spending_investment_share_panel` | SUPPORTED | coef=-0.2038 | p=0.005161 | q=0.03303 | n=1282
- `market_order_government_spending_gdp_pc_growth_panel` | SUPPORTED | coef=-0.2569 | p=1.517e-09 | q=4.855e-08 | n=1282
- `market_order_government_spending_private_credit_depth_panel` | REFUTED | coef=+1.688 | p=0.01212 | q=0.06464 | n=1092
- `market_order_government_spending_employment_rate_panel` | SUPPORTED | coef=-0.1949 | p=0.0001871 | q=0.002993 | n=1282
- `market_order_tax_burden_investment_share_panel` | PARTIAL | coef=+0.1453 | p=0.487 | q=0.685 | n=1313
- `market_order_tax_burden_gdp_pc_growth_panel` | PARTIAL | coef=+0.058 | p=0.3938 | q=0.6632 | n=1313
- `market_order_tax_burden_private_credit_depth_panel` | PARTIAL | coef=+1.447 | p=0.2825 | q=0.6458 | n=1111
- `market_order_tax_burden_employment_rate_panel` | PARTIAL | coef=+0.06295 | p=0.622 | q=0.7109 | n=1313
- `market_order_trade_openness_investment_share_panel` | PARTIAL | coef=-0.02107 | p=0.3309 | q=0.653 | n=1453
- `market_order_trade_openness_gdp_pc_growth_panel` | PARTIAL | coef=+0.008016 | p=0.3226 | q=0.653 | n=1453
- `market_order_trade_openness_high_tech_exports_panel` | PARTIAL | coef=+0.01609 | p=0.5008 | q=0.685 | n=845
- `market_order_trade_openness_employment_rate_panel` | PARTIAL | coef=-0.009689 | p=0.5004 | q=0.685 | n=1453
