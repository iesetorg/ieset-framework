# EFW OECD/Market Panel Results - 2026-05-03

## Methodology Gate

- Pre-registration commit: `4a7635cb`
- Runner commit at estimation: `4a7635cb`
- Estimation was run only after the 108 specs and steelmen were committed.
- No school-scoreboard mappings were asserted in this wave.
- Each run directory includes `diagnostics.json`, `result_card.md`, and `replication.py`.

## Counts

- PARTIAL: 74
- REFUTED: 7
- SUPPORTED: 27

## FDR q<=0.10

- REFUTED: 2
- SUPPORTED: 12

## FDR q<=0.05

- REFUTED: 2
- SUPPORTED: 11

## By Mechanism

- efw_summary: PARTIAL=10, REFUTED=1, SUPPORTED=7
- property_rights: PARTIAL=13, REFUTED=4, SUPPORTED=1
- regulation: PARTIAL=12, REFUTED=1, SUPPORTED=5
- size_government: PARTIAL=9, SUPPORTED=9
- sound_money: PARTIAL=13, REFUTED=1, SUPPORTED=4
- trade_freedom: PARTIAL=17, SUPPORTED=1

## By Outcome

- child_mortality: PARTIAL=4, SUPPORTED=2
- employment_rate: PARTIAL=4, REFUTED=1, SUPPORTED=1
- export_growth: PARTIAL=5, SUPPORTED=1
- fdi_inflows_share: PARTIAL=6
- gdp_growth: PARTIAL=3, SUPPORTED=3
- gdp_pc_growth: PARTIAL=3, SUPPORTED=3
- gni_pc_growth: PARTIAL=2, REFUTED=1, SUPPORTED=3
- gross_capital_formation: PARTIAL=4, REFUTED=1, SUPPORTED=1
- gross_savings_share: PARTIAL=3, REFUTED=1, SUPPORTED=2
- high_tech_exports: PARTIAL=5, SUPPORTED=1
- industry_employment: PARTIAL=3, SUPPORTED=3
- inflation_rate: PARTIAL=4, SUPPORTED=2
- investment_share: PARTIAL=5, SUPPORTED=1
- life_expectancy: PARTIAL=6
- manufacturing_share: PARTIAL=3, REFUTED=1, SUPPORTED=2
- nonperforming_loans: PARTIAL=5, SUPPORTED=1
- private_credit_depth: PARTIAL=4, REFUTED=2
- services_value_added: PARTIAL=5, SUPPORTED=1

## Results

- `efw_oecd_panel_efw_summary_gdp_pc_growth_20260503`: SUPPORTED | coef=+1.214 | p=0.02342 | q=0.1331 | n=1032 | countries=40
- `efw_oecd_panel_efw_summary_gdp_growth_20260503`: SUPPORTED | coef=+1.225 | p=0.02257 | q=0.1331 | n=1032 | countries=40
- `efw_oecd_panel_efw_summary_gni_pc_growth_20260503`: SUPPORTED | coef=+1.922 | p=0.002598 | q=0.02338 | n=967 | countries=39; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_efw_summary_investment_share_20260503`: PARTIAL | coef=+0.5841 | p=0.4976 | q=0.6717 | n=1032 | countries=40
- `efw_oecd_panel_efw_summary_gross_capital_formation_20260503`: PARTIAL | coef=+0.03497 | p=0.9584 | q=0.9765 | n=1032 | countries=40
- `efw_oecd_panel_efw_summary_gross_savings_share_20260503`: PARTIAL | coef=+0.4721 | p=0.4808 | q=0.6578 | n=1010 | countries=40
- `efw_oecd_panel_efw_summary_private_credit_depth_20260503`: REFUTED | coef=-12.84 | p=0.03683 | q=0.1729 | n=894 | countries=40
- `efw_oecd_panel_efw_summary_employment_rate_20260503`: PARTIAL | coef=-0.9204 | p=0.2386 | q=0.4653 | n=1000 | countries=40
- `efw_oecd_panel_efw_summary_industry_employment_20260503`: SUPPORTED | coef=+1.117 | p=0.07851 | q=0.2735 | n=1000 | countries=40
- `efw_oecd_panel_efw_summary_manufacturing_share_20260503`: PARTIAL | coef=+0.1319 | p=0.8708 | q=0.9404 | n=1014 | countries=40
- `efw_oecd_panel_efw_summary_services_value_added_20260503`: PARTIAL | coef=+1.374 | p=0.3207 | q=0.5413 | n=1015 | countries=40
- `efw_oecd_panel_efw_summary_high_tech_exports_20260503`: PARTIAL | coef=-2.679 | p=0.4576 | q=0.6578 | n=679 | countries=40
- `efw_oecd_panel_efw_summary_fdi_inflows_share_20260503`: PARTIAL | coef=-0.09841 | p=0.9085 | q=0.947 | n=1034 | countries=40
- `efw_oecd_panel_efw_summary_export_growth_20260503`: SUPPORTED | coef=+1.307 | p=0.07824 | q=0.2735 | n=1028 | countries=40
- `efw_oecd_panel_efw_summary_life_expectancy_20260503`: PARTIAL | coef=-0.1221 | p=0.5407 | q=0.6871 | n=1037 | countries=40
- `efw_oecd_panel_efw_summary_child_mortality_20260503`: SUPPORTED | coef=-2.087 | p=0.04614 | q=0.1993 | n=1037 | countries=40
- `efw_oecd_panel_efw_summary_inflation_rate_20260503`: SUPPORTED | coef=-29.63 | p=0.07488 | q=0.2735 | n=1033 | countries=40
- `efw_oecd_panel_efw_summary_nonperforming_loans_20260503`: PARTIAL | coef=-5.223 | p=0.2051 | q=0.4216 | n=604 | countries=39
- `efw_oecd_panel_size_government_gdp_pc_growth_20260503`: SUPPORTED | coef=+1.216 | p=0.001996 | q=0.02338 | n=1032 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_gdp_growth_20260503`: SUPPORTED | coef=+1.219 | p=0.001981 | q=0.02338 | n=1032 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_gni_pc_growth_20260503`: SUPPORTED | coef=+1.66 | p=0.001266 | q=0.02278 | n=967 | countries=39; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_investment_share_20260503`: SUPPORTED | coef=+1.692 | p=0.0008464 | q=0.01828 | n=1034 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_gross_capital_formation_20260503`: SUPPORTED | coef=+1.701 | p=0.002598 | q=0.02338 | n=1034 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_gross_savings_share_20260503`: SUPPORTED | coef=+1.864 | p=0.002518 | q=0.02338 | n=1010 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_size_government_private_credit_depth_20260503`: PARTIAL | coef=-5.249 | p=0.245 | q=0.4653 | n=894 | countries=40
- `efw_oecd_panel_size_government_employment_rate_20260503`: SUPPORTED | coef=+1.057 | p=0.03656 | q=0.1729 | n=1000 | countries=40
- `efw_oecd_panel_size_government_industry_employment_20260503`: SUPPORTED | coef=+0.7888 | p=0.03918 | q=0.1763 | n=1000 | countries=40
- `efw_oecd_panel_size_government_manufacturing_share_20260503`: SUPPORTED | coef=+0.8019 | p=0.07504 | q=0.2735 | n=1014 | countries=40
- `efw_oecd_panel_size_government_services_value_added_20260503`: PARTIAL | coef=-0.09169 | p=0.9119 | q=0.947 | n=1015 | countries=40
- `efw_oecd_panel_size_government_high_tech_exports_20260503`: PARTIAL | coef=-0.8873 | p=0.3388 | q=0.5598 | n=679 | countries=40
- `efw_oecd_panel_size_government_fdi_inflows_share_20260503`: PARTIAL | coef=-0.6135 | p=0.4812 | q=0.6578 | n=1034 | countries=40
- `efw_oecd_panel_size_government_export_growth_20260503`: PARTIAL | coef=+0.6936 | p=0.2985 | q=0.5292 | n=1028 | countries=40
- `efw_oecd_panel_size_government_life_expectancy_20260503`: PARTIAL | coef=-0.2192 | p=0.2069 | q=0.4216 | n=1039 | countries=40
- `efw_oecd_panel_size_government_child_mortality_20260503`: PARTIAL | coef=+0.5145 | p=0.5089 | q=0.6785 | n=1039 | countries=40
- `efw_oecd_panel_size_government_inflation_rate_20260503`: PARTIAL | coef=-19.85 | p=0.1064 | q=0.3192 | n=1034 | countries=40
- `efw_oecd_panel_size_government_nonperforming_loans_20260503`: PARTIAL | coef=-2.876 | p=0.1613 | q=0.3958 | n=604 | countries=39
- `efw_oecd_panel_property_rights_gdp_pc_growth_20260503`: PARTIAL | coef=-0.5428 | p=0.3147 | q=0.5413 | n=1032 | countries=40
- `efw_oecd_panel_property_rights_gdp_growth_20260503`: PARTIAL | coef=-0.5411 | p=0.3186 | q=0.5413 | n=1032 | countries=40
- `efw_oecd_panel_property_rights_gni_pc_growth_20260503`: REFUTED | coef=-1.15 | p=0.09054 | q=0.2963 | n=967 | countries=39
- `efw_oecd_panel_property_rights_investment_share_20260503`: PARTIAL | coef=-1.53 | p=0.1052 | q=0.3192 | n=1035 | countries=40
- `efw_oecd_panel_property_rights_gross_capital_formation_20260503`: REFUTED | coef=-1.777 | p=0.06301 | q=0.2618 | n=1035 | countries=40
- `efw_oecd_panel_property_rights_gross_savings_share_20260503`: REFUTED | coef=-1.919 | p=0.01657 | q=0.1193 | n=1010 | countries=40
- `efw_oecd_panel_property_rights_private_credit_depth_20260503`: PARTIAL | coef=+2.91 | p=0.6551 | q=0.7691 | n=894 | countries=40
- `efw_oecd_panel_property_rights_employment_rate_20260503`: PARTIAL | coef=-0.2328 | p=0.7649 | q=0.8789 | n=1000 | countries=40
- `efw_oecd_panel_property_rights_industry_employment_20260503`: PARTIAL | coef=-0.7979 | p=0.2047 | q=0.4216 | n=1000 | countries=40
- `efw_oecd_panel_property_rights_manufacturing_share_20260503`: REFUTED | coef=-1.398 | p=0.02996 | q=0.1618 | n=1014 | countries=40
- `efw_oecd_panel_property_rights_services_value_added_20260503`: SUPPORTED | coef=+2.932 | p=0.009723 | q=0.075 | n=1015 | countries=40; FDR q<=0.10
- `efw_oecd_panel_property_rights_high_tech_exports_20260503`: PARTIAL | coef=-0.08393 | p=0.9773 | q=0.9773 | n=679 | countries=40
- `efw_oecd_panel_property_rights_fdi_inflows_share_20260503`: PARTIAL | coef=-2.014 | p=0.1421 | q=0.3742 | n=1034 | countries=40
- `efw_oecd_panel_property_rights_export_growth_20260503`: PARTIAL | coef=+0.8539 | p=0.4774 | q=0.6578 | n=1028 | countries=40
- `efw_oecd_panel_property_rights_life_expectancy_20260503`: PARTIAL | coef=+0.04508 | p=0.9033 | q=0.947 | n=1040 | countries=40
- `efw_oecd_panel_property_rights_child_mortality_20260503`: PARTIAL | coef=+2.192 | p=0.192 | q=0.4216 | n=1040 | countries=40
- `efw_oecd_panel_property_rights_inflation_rate_20260503`: PARTIAL | coef=-10.65 | p=0.2064 | q=0.4216 | n=1034 | countries=40
- `efw_oecd_panel_property_rights_nonperforming_loans_20260503`: PARTIAL | coef=-2.469 | p=0.2462 | q=0.4653 | n=604 | countries=39
- `efw_oecd_panel_sound_money_gdp_pc_growth_20260503`: PARTIAL | coef=+0.1848 | p=0.1605 | q=0.3958 | n=1032 | countries=40
- `efw_oecd_panel_sound_money_gdp_growth_20260503`: PARTIAL | coef=+0.1863 | p=0.1585 | q=0.3958 | n=1032 | countries=40
- `efw_oecd_panel_sound_money_gni_pc_growth_20260503`: SUPPORTED | coef=+0.3329 | p=0.08221 | q=0.2774 | n=967 | countries=39
- `efw_oecd_panel_sound_money_investment_share_20260503`: PARTIAL | coef=+0.1371 | p=0.5517 | q=0.6929 | n=1033 | countries=40
- `efw_oecd_panel_sound_money_gross_capital_formation_20260503`: PARTIAL | coef=+0.02719 | p=0.9027 | q=0.947 | n=1033 | countries=40
- `efw_oecd_panel_sound_money_gross_savings_share_20260503`: PARTIAL | coef=-0.1499 | p=0.4265 | q=0.6578 | n=1010 | countries=40
- `efw_oecd_panel_sound_money_private_credit_depth_20260503`: PARTIAL | coef=-2.763 | p=0.2499 | q=0.4653 | n=894 | countries=40
- `efw_oecd_panel_sound_money_employment_rate_20260503`: REFUTED | coef=-0.7622 | p=2.275e-05 | q=0.000819 | n=1000 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_sound_money_industry_employment_20260503`: SUPPORTED | coef=+0.3254 | p=0.07286 | q=0.2735 | n=1000 | countries=40
- `efw_oecd_panel_sound_money_manufacturing_share_20260503`: PARTIAL | coef=-0.1828 | p=0.465 | q=0.6578 | n=1014 | countries=40
- `efw_oecd_panel_sound_money_services_value_added_20260503`: PARTIAL | coef=+0.2505 | p=0.2824 | q=0.517 | n=1015 | countries=40
- `efw_oecd_panel_sound_money_high_tech_exports_20260503`: PARTIAL | coef=-1.468 | p=0.3608 | q=0.573 | n=679 | countries=40
- `efw_oecd_panel_sound_money_fdi_inflows_share_20260503`: PARTIAL | coef=+0.04721 | p=0.8113 | q=0.894 | n=1034 | countries=40
- `efw_oecd_panel_sound_money_export_growth_20260503`: PARTIAL | coef=+0.1743 | p=0.5384 | q=0.6871 | n=1028 | countries=40
- `efw_oecd_panel_sound_money_life_expectancy_20260503`: PARTIAL | coef=+0.06358 | p=0.353 | q=0.5691 | n=1038 | countries=40
- `efw_oecd_panel_sound_money_child_mortality_20260503`: SUPPORTED | coef=-1.432 | p=1.184e-05 | q=0.0006566 | n=1038 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_sound_money_inflation_rate_20260503`: SUPPORTED | coef=-7.379 | p=0.00217 | q=0.02338 | n=1033 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_sound_money_nonperforming_loans_20260503`: PARTIAL | coef=-0.6183 | p=0.5191 | q=0.6835 | n=604 | countries=39
- `efw_oecd_panel_trade_freedom_gdp_pc_growth_20260503`: PARTIAL | coef=+0.2461 | p=0.4723 | q=0.6578 | n=1032 | countries=40
- `efw_oecd_panel_trade_freedom_gdp_growth_20260503`: PARTIAL | coef=+0.251 | p=0.4655 | q=0.6578 | n=1032 | countries=40
- `efw_oecd_panel_trade_freedom_gni_pc_growth_20260503`: PARTIAL | coef=+0.7668 | p=0.1198 | q=0.3317 | n=967 | countries=39
- `efw_oecd_panel_trade_freedom_investment_share_20260503`: PARTIAL | coef=+0.1272 | p=0.7955 | q=0.8857 | n=1032 | countries=40
- `efw_oecd_panel_trade_freedom_gross_capital_formation_20260503`: PARTIAL | coef=-0.2395 | p=0.5253 | q=0.6835 | n=1032 | countries=40
- `efw_oecd_panel_trade_freedom_gross_savings_share_20260503`: PARTIAL | coef=-0.1202 | p=0.7768 | q=0.8828 | n=1010 | countries=40
- `efw_oecd_panel_trade_freedom_private_credit_depth_20260503`: PARTIAL | coef=-2.536 | p=0.5972 | q=0.7176 | n=894 | countries=40
- `efw_oecd_panel_trade_freedom_employment_rate_20260503`: PARTIAL | coef=+0.7004 | p=0.2989 | q=0.5292 | n=1000 | countries=40
- `efw_oecd_panel_trade_freedom_industry_employment_20260503`: PARTIAL | coef=+0.4388 | p=0.1169 | q=0.3317 | n=1000 | countries=40
- `efw_oecd_panel_trade_freedom_manufacturing_share_20260503`: PARTIAL | coef=-0.01609 | p=0.9706 | q=0.9773 | n=1014 | countries=40
- `efw_oecd_panel_trade_freedom_services_value_added_20260503`: PARTIAL | coef=+0.5667 | p=0.571 | q=0.704 | n=1015 | countries=40
- `efw_oecd_panel_trade_freedom_high_tech_exports_20260503`: PARTIAL | coef=-0.08288 | p=0.9576 | q=0.9765 | n=679 | countries=40
- `efw_oecd_panel_trade_freedom_fdi_inflows_share_20260503`: PARTIAL | coef=+0.2444 | p=0.6047 | q=0.7176 | n=1034 | countries=40
- `efw_oecd_panel_trade_freedom_export_growth_20260503`: PARTIAL | coef=+0.4211 | p=0.4376 | q=0.6578 | n=1028 | countries=40
- `efw_oecd_panel_trade_freedom_life_expectancy_20260503`: PARTIAL | coef=-0.1451 | p=0.2303 | q=0.4606 | n=1035 | countries=40
- `efw_oecd_panel_trade_freedom_child_mortality_20260503`: PARTIAL | coef=-0.5061 | p=0.4625 | q=0.6578 | n=1035 | countries=40
- `efw_oecd_panel_trade_freedom_inflation_rate_20260503`: PARTIAL | coef=-7.3 | p=0.1243 | q=0.3357 | n=1033 | countries=40
- `efw_oecd_panel_trade_freedom_nonperforming_loans_20260503`: SUPPORTED | coef=-4.303 | p=0.03444 | q=0.1729 | n=604 | countries=39
- `efw_oecd_panel_regulation_gdp_pc_growth_20260503`: SUPPORTED | coef=+0.8613 | p=0.02273 | q=0.1331 | n=1032 | countries=40
- `efw_oecd_panel_regulation_gdp_growth_20260503`: SUPPORTED | coef=+0.8736 | p=0.02206 | q=0.1331 | n=1032 | countries=40
- `efw_oecd_panel_regulation_gni_pc_growth_20260503`: PARTIAL | coef=+0.7989 | p=0.1769 | q=0.4117 | n=967 | countries=39
- `efw_oecd_panel_regulation_investment_share_20260503`: PARTIAL | coef=-0.7799 | p=0.183 | q=0.4117 | n=1034 | countries=40
- `efw_oecd_panel_regulation_gross_capital_formation_20260503`: PARTIAL | coef=-0.8496 | p=0.115 | q=0.3317 | n=1034 | countries=40
- `efw_oecd_panel_regulation_gross_savings_share_20260503`: SUPPORTED | coef=+1.356 | p=0.09885 | q=0.314 | n=1010 | countries=40
- `efw_oecd_panel_regulation_private_credit_depth_20260503`: REFUTED | coef=-17.48 | p=7.606e-05 | q=0.002054 | n=894 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_regulation_employment_rate_20260503`: PARTIAL | coef=+0.2973 | p=0.7002 | q=0.8131 | n=1000 | countries=40
- `efw_oecd_panel_regulation_industry_employment_20260503`: PARTIAL | coef=-0.381 | p=0.4301 | q=0.6578 | n=1000 | countries=40
- `efw_oecd_panel_regulation_manufacturing_share_20260503`: SUPPORTED | coef=+1.404 | p=1.216e-05 | q=0.0006566 | n=1014 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_regulation_services_value_added_20260503`: PARTIAL | coef=-0.2076 | p=0.7848 | q=0.8828 | n=1015 | countries=40
- `efw_oecd_panel_regulation_high_tech_exports_20260503`: SUPPORTED | coef=+3.131 | p=0.005659 | q=0.04702 | n=679 | countries=40; FDR q<=0.10; FDR q<=0.05
- `efw_oecd_panel_regulation_fdi_inflows_share_20260503`: PARTIAL | coef=+1.078 | p=0.1694 | q=0.4066 | n=1034 | countries=40
- `efw_oecd_panel_regulation_export_growth_20260503`: PARTIAL | coef=+0.8255 | p=0.3421 | q=0.5598 | n=1028 | countries=40
- `efw_oecd_panel_regulation_life_expectancy_20260503`: PARTIAL | coef=-0.1374 | p=0.5737 | q=0.704 | n=1039 | countries=40
- `efw_oecd_panel_regulation_child_mortality_20260503`: PARTIAL | coef=+0.8519 | p=0.5986 | q=0.7176 | n=1039 | countries=40
- `efw_oecd_panel_regulation_inflation_rate_20260503`: PARTIAL | coef=-3.43 | p=0.825 | q=0.9 | n=1034 | countries=40
- `efw_oecd_panel_regulation_nonperforming_loans_20260503`: PARTIAL | coef=+3.108 | p=0.1814 | q=0.4117 | n=604 | countries=39
