# EFW Market Panel Results - 2026-05-03

## Methodology Gate

- Pre-registration commit: `61fcff11`
- Runner commit at estimation: `61fcff11`
- Estimation was run only after the 78 specs and steelmen were committed.
- No school-scoreboard mappings were asserted in this wave.
- Each run directory includes `diagnostics.json`, `result_card.md`, and `replication.py`.

## Counts

- PARTIAL: 62
- REFUTED: 6
- SUPPORTED: 10

## FDR q<=0.10

- REFUTED: 1
- SUPPORTED: 3

## FDR q<=0.05

- REFUTED: 1
- SUPPORTED: 2

## By Mechanism

- efw_summary: PARTIAL=9, REFUTED=2, SUPPORTED=2
- property_rights: PARTIAL=11, REFUTED=1, SUPPORTED=1
- regulation: PARTIAL=11, REFUTED=1, SUPPORTED=1
- size_government: PARTIAL=10, REFUTED=1, SUPPORTED=2
- sound_money: PARTIAL=10, REFUTED=1, SUPPORTED=2
- trade_freedom: PARTIAL=11, SUPPORTED=2

## By Outcome

- child_mortality: PARTIAL=3, SUPPORTED=3
- employment_rate: PARTIAL=5, SUPPORTED=1
- export_growth: PARTIAL=6
- fdi_inflows_share: PARTIAL=6
- gdp_pc_growth: PARTIAL=4, SUPPORTED=2
- gross_savings_share: PARTIAL=4, REFUTED=2
- high_tech_exports: PARTIAL=5, SUPPORTED=1
- inflation_rate: PARTIAL=6
- investment_share: PARTIAL=6
- life_expectancy: PARTIAL=6
- manufacturing_share: PARTIAL=4, REFUTED=2
- poverty_365: PARTIAL=3, SUPPORTED=3
- private_credit_depth: PARTIAL=4, REFUTED=2

## Results

- `efw_market_panel_efw_summary_gdp_pc_growth_20260503`: PARTIAL | coef=+0.3939 | p=0.2703 | q=0.6087 | n=1496 | countries=59
- `efw_market_panel_efw_summary_investment_share_20260503`: PARTIAL | coef=+0.004671 | p=0.995 | q=0.995 | n=1494 | countries=59
- `efw_market_panel_efw_summary_gross_savings_share_20260503`: REFUTED | coef=-1.35 | p=0.04912 | q=0.4712 | n=1474 | countries=59
- `efw_market_panel_efw_summary_private_credit_depth_20260503`: PARTIAL | coef=-4.554 | p=0.1929 | q=0.6087 | n=1304 | countries=59
- `efw_market_panel_efw_summary_employment_rate_20260503`: PARTIAL | coef=+0.1565 | p=0.8537 | q=0.9513 | n=1449 | countries=59
- `efw_market_panel_efw_summary_manufacturing_share_20260503`: REFUTED | coef=-0.7081 | p=0.09036 | q=0.4712 | n=1464 | countries=59
- `efw_market_panel_efw_summary_high_tech_exports_20260503`: PARTIAL | coef=+0.7383 | p=0.634 | q=0.8991 | n=938 | countries=59
- `efw_market_panel_efw_summary_fdi_inflows_share_20260503`: PARTIAL | coef=+0.122 | p=0.7853 | q=0.9513 | n=1496 | countries=59
- `efw_market_panel_efw_summary_export_growth_20260503`: PARTIAL | coef=+1.187 | p=0.2427 | q=0.6087 | n=1456 | countries=58
- `efw_market_panel_efw_summary_life_expectancy_20260503`: PARTIAL | coef=+0.1486 | p=0.4945 | q=0.8603 | n=1496 | countries=59
- `efw_market_panel_efw_summary_child_mortality_20260503`: SUPPORTED | coef=-3.6 | p=0.03312 | q=0.4306 | n=1496 | countries=59
- `efw_market_panel_efw_summary_poverty_365_20260503`: SUPPORTED | coef=-6.99 | p=3.217e-05 | q=0.002509 | n=1036 | countries=56; FDR q<=0.10; FDR q<=0.05
- `efw_market_panel_efw_summary_inflation_rate_20260503`: PARTIAL | coef=-241.9 | p=0.1554 | q=0.6059 | n=1496 | countries=59
- `efw_market_panel_size_government_gdp_pc_growth_20260503`: SUPPORTED | coef=+0.6205 | p=0.08742 | q=0.4712 | n=1501 | countries=59
- `efw_market_panel_size_government_investment_share_20260503`: PARTIAL | coef=+0.1433 | p=0.8148 | q=0.9513 | n=1500 | countries=59
- `efw_market_panel_size_government_gross_savings_share_20260503`: PARTIAL | coef=-0.2029 | p=0.7412 | q=0.9494 | n=1479 | countries=59
- `efw_market_panel_size_government_private_credit_depth_20260503`: REFUTED | coef=-4.865 | p=0.06023 | q=0.4712 | n=1309 | countries=59
- `efw_market_panel_size_government_employment_rate_20260503`: PARTIAL | coef=-0.06585 | p=0.9201 | q=0.9596 | n=1453 | countries=59
- `efw_market_panel_size_government_manufacturing_share_20260503`: PARTIAL | coef=+0.2537 | p=0.5781 | q=0.8936 | n=1467 | countries=59
- `efw_market_panel_size_government_high_tech_exports_20260503`: PARTIAL | coef=-0.2568 | p=0.7231 | q=0.9494 | n=941 | countries=59
- `efw_market_panel_size_government_fdi_inflows_share_20260503`: PARTIAL | coef=-0.2074 | p=0.6212 | q=0.8991 | n=1501 | countries=59
- `efw_market_panel_size_government_export_growth_20260503`: PARTIAL | coef=+0.3111 | p=0.5184 | q=0.8603 | n=1459 | countries=58
- `efw_market_panel_size_government_life_expectancy_20260503`: PARTIAL | coef=-0.0826 | p=0.5099 | q=0.8603 | n=1502 | countries=59
- `efw_market_panel_size_government_child_mortality_20260503`: SUPPORTED | coef=-3.417 | p=0.06565 | q=0.4712 | n=1502 | countries=59
- `efw_market_panel_size_government_poverty_365_20260503`: PARTIAL | coef=-0.2323 | p=0.8359 | q=0.9513 | n=1037 | countries=56
- `efw_market_panel_size_government_inflation_rate_20260503`: PARTIAL | coef=-13.64 | p=0.2708 | q=0.6087 | n=1502 | countries=59
- `efw_market_panel_property_rights_gdp_pc_growth_20260503`: PARTIAL | coef=-0.1789 | p=0.5843 | q=0.8936 | n=1498 | countries=59
- `efw_market_panel_property_rights_investment_share_20260503`: PARTIAL | coef=+0.2334 | p=0.7425 | q=0.9494 | n=1497 | countries=59
- `efw_market_panel_property_rights_gross_savings_share_20260503`: REFUTED | coef=-1.573 | p=0.0998 | q=0.4712 | n=1476 | countries=59
- `efw_market_panel_property_rights_private_credit_depth_20260503`: PARTIAL | coef=-2.593 | p=0.5834 | q=0.8936 | n=1306 | countries=59
- `efw_market_panel_property_rights_employment_rate_20260503`: SUPPORTED | coef=+1.831 | p=0.06703 | q=0.4712 | n=1450 | countries=59
- `efw_market_panel_property_rights_manufacturing_share_20260503`: PARTIAL | coef=+0.1271 | p=0.8464 | q=0.9513 | n=1466 | countries=59
- `efw_market_panel_property_rights_high_tech_exports_20260503`: PARTIAL | coef=+0.5336 | p=0.6244 | q=0.8991 | n=938 | countries=59
- `efw_market_panel_property_rights_fdi_inflows_share_20260503`: PARTIAL | coef=-0.3891 | p=0.5449 | q=0.8855 | n=1498 | countries=59
- `efw_market_panel_property_rights_export_growth_20260503`: PARTIAL | coef=+1.236 | p=0.1322 | q=0.5427 | n=1456 | countries=58
- `efw_market_panel_property_rights_life_expectancy_20260503`: PARTIAL | coef=+0.3219 | p=0.2439 | q=0.6087 | n=1499 | countries=59
- `efw_market_panel_property_rights_child_mortality_20260503`: PARTIAL | coef=-2.283 | p=0.2809 | q=0.6087 | n=1499 | countries=59
- `efw_market_panel_property_rights_poverty_365_20260503`: PARTIAL | coef=-0.6916 | p=0.7241 | q=0.9494 | n=1036 | countries=56
- `efw_market_panel_property_rights_inflation_rate_20260503`: PARTIAL | coef=-44.55 | p=0.3263 | q=0.6698 | n=1499 | countries=59
- `efw_market_panel_sound_money_gdp_pc_growth_20260503`: SUPPORTED | coef=+0.1753 | p=0.09872 | q=0.4712 | n=1517 | countries=59
- `efw_market_panel_sound_money_investment_share_20260503`: PARTIAL | coef=-0.01361 | p=0.935 | q=0.9596 | n=1517 | countries=59
- `efw_market_panel_sound_money_gross_savings_share_20260503`: PARTIAL | coef=-0.2451 | p=0.1939 | q=0.6087 | n=1495 | countries=59
- `efw_market_panel_sound_money_private_credit_depth_20260503`: PARTIAL | coef=+0.1895 | p=0.8363 | q=0.9513 | n=1324 | countries=59
- `efw_market_panel_sound_money_employment_rate_20260503`: PARTIAL | coef=-0.2113 | p=0.2782 | q=0.6087 | n=1468 | countries=59
- `efw_market_panel_sound_money_manufacturing_share_20260503`: REFUTED | coef=-0.3847 | p=0.001904 | q=0.04951 | n=1484 | countries=59; FDR q<=0.10; FDR q<=0.05
- `efw_market_panel_sound_money_high_tech_exports_20260503`: PARTIAL | coef=+0.1458 | p=0.8352 | q=0.9513 | n=949 | countries=59
- `efw_market_panel_sound_money_fdi_inflows_share_20260503`: PARTIAL | coef=+0.09034 | p=0.3068 | q=0.6468 | n=1517 | countries=59
- `efw_market_panel_sound_money_export_growth_20260503`: PARTIAL | coef=+0.5 | p=0.2078 | q=0.6087 | n=1476 | countries=58
- `efw_market_panel_sound_money_life_expectancy_20260503`: PARTIAL | coef=+0.07225 | p=0.274 | q=0.6087 | n=1519 | countries=59
- `efw_market_panel_sound_money_child_mortality_20260503`: PARTIAL | coef=+0.09044 | p=0.8787 | q=0.9519 | n=1519 | countries=59
- `efw_market_panel_sound_money_poverty_365_20260503`: SUPPORTED | coef=-1.679 | p=0.002959 | q=0.05771 | n=1054 | countries=56; FDR q<=0.10
- `efw_market_panel_sound_money_inflation_rate_20260503`: PARTIAL | coef=-61.61 | p=0.119 | q=0.5159 | n=1496 | countries=59
- `efw_market_panel_trade_freedom_gdp_pc_growth_20260503`: PARTIAL | coef=+0.1554 | p=0.4467 | q=0.8297 | n=1482 | countries=59
- `efw_market_panel_trade_freedom_investment_share_20260503`: PARTIAL | coef=+0.2129 | p=0.6271 | q=0.8991 | n=1480 | countries=59
- `efw_market_panel_trade_freedom_gross_savings_share_20260503`: PARTIAL | coef=-0.1586 | p=0.7886 | q=0.9513 | n=1460 | countries=59
- `efw_market_panel_trade_freedom_private_credit_depth_20260503`: PARTIAL | coef=-3.482 | p=0.1027 | q=0.4712 | n=1291 | countries=59
- `efw_market_panel_trade_freedom_employment_rate_20260503`: PARTIAL | coef=+0.4382 | p=0.2593 | q=0.6087 | n=1435 | countries=59
- `efw_market_panel_trade_freedom_manufacturing_share_20260503`: PARTIAL | coef=+0.2368 | p=0.3841 | q=0.737 | n=1453 | countries=59
- `efw_market_panel_trade_freedom_high_tech_exports_20260503`: PARTIAL | coef=+0.3056 | p=0.658 | q=0.9004 | n=935 | countries=59
- `efw_market_panel_trade_freedom_fdi_inflows_share_20260503`: PARTIAL | coef=-0.0325 | p=0.9157 | q=0.9596 | n=1482 | countries=59
- `efw_market_panel_trade_freedom_export_growth_20260503`: PARTIAL | coef=+0.6866 | p=0.1959 | q=0.6087 | n=1443 | countries=58
- `efw_market_panel_trade_freedom_life_expectancy_20260503`: PARTIAL | coef=+0.231 | p=0.1657 | q=0.6087 | n=1482 | countries=59
- `efw_market_panel_trade_freedom_child_mortality_20260503`: SUPPORTED | coef=-4.746 | p=0.000664 | q=0.0259 | n=1482 | countries=59; FDR q<=0.10; FDR q<=0.05
- `efw_market_panel_trade_freedom_poverty_365_20260503`: SUPPORTED | coef=-2.098 | p=0.07885 | q=0.4712 | n=1034 | countries=56
- `efw_market_panel_trade_freedom_inflation_rate_20260503`: PARTIAL | coef=-121.2 | p=0.2195 | q=0.6087 | n=1482 | countries=59
- `efw_market_panel_regulation_gdp_pc_growth_20260503`: PARTIAL | coef=+0.1986 | p=0.5062 | q=0.8603 | n=1498 | countries=59
- `efw_market_panel_regulation_investment_share_20260503`: PARTIAL | coef=-0.01705 | p=0.982 | q=0.9947 | n=1497 | countries=59
- `efw_market_panel_regulation_gross_savings_share_20260503`: PARTIAL | coef=+0.7904 | p=0.3874 | q=0.737 | n=1476 | countries=59
- `efw_market_panel_regulation_private_credit_depth_20260503`: REFUTED | coef=-6.819 | p=0.09308 | q=0.4712 | n=1306 | countries=59
- `efw_market_panel_regulation_employment_rate_20260503`: PARTIAL | coef=-0.06119 | p=0.9279 | q=0.9596 | n=1450 | countries=59
- `efw_market_panel_regulation_manufacturing_share_20260503`: PARTIAL | coef=-0.2901 | p=0.4689 | q=0.8505 | n=1466 | countries=59
- `efw_market_panel_regulation_high_tech_exports_20260503`: SUPPORTED | coef=+2.261 | p=0.01566 | q=0.2443 | n=938 | countries=59
- `efw_market_panel_regulation_fdi_inflows_share_20260503`: PARTIAL | coef=+0.5093 | p=0.384 | q=0.737 | n=1498 | countries=59
- `efw_market_panel_regulation_export_growth_20260503`: PARTIAL | coef=+0.1453 | p=0.8665 | q=0.9519 | n=1456 | countries=58
- `efw_market_panel_regulation_life_expectancy_20260503`: PARTIAL | coef=-0.1055 | p=0.6499 | q=0.9004 | n=1499 | countries=59
- `efw_market_panel_regulation_child_mortality_20260503`: PARTIAL | coef=-0.5739 | p=0.7829 | q=0.9513 | n=1499 | countries=59
- `efw_market_panel_regulation_poverty_365_20260503`: PARTIAL | coef=-2.083 | p=0.2257 | q=0.6087 | n=1036 | countries=56
- `efw_market_panel_regulation_inflation_rate_20260503`: PARTIAL | coef=-162.3 | p=0.2499 | q=0.6087 | n=1499 | countries=59
