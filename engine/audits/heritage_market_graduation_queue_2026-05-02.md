# Heritage Market Pre-Registration Queue - 2026-05-02

## Methodology Gate

- Scoreboard status: not eligible.
- These are post-estimation candidate screens, not scoreboard claims.
- Do not create position `falsifiable_specific_claims` or hypothesis `covers_claims` from this queue.
- To advance: register a stronger panel/event spec before estimation, then run and validate it.

## Selection Rule

- Top 50 controlled supports with BH/FDR q<=0.10.
- All controlled refutations with BH/FDR q<=0.10.
- Purpose: identify which Heritage market-order results deserve stronger panel/event designs and which fiscal-size claims should be respecified rather than promoted.

## Counts

- graduate_to_panel_fe_or_event_design: 50
- respec_or_counter_hypothesis: 14

## Component Mix

- business_freedom: {'graduate_to_panel_fe_or_event_design': 7}
- financial_freedom: {'graduate_to_panel_fe_or_event_design': 6, 'respec_or_counter_hypothesis': 1}
- government_integrity: {'graduate_to_panel_fe_or_event_design': 6, 'respec_or_counter_hypothesis': 1}
- government_spending: {'respec_or_counter_hypothesis': 5}
- investment_freedom: {'graduate_to_panel_fe_or_event_design': 3}
- judicial_effectiveness: {'graduate_to_panel_fe_or_event_design': 5, 'respec_or_counter_hypothesis': 1}
- monetary_freedom: {'graduate_to_panel_fe_or_event_design': 4}
- overall_score: {'graduate_to_panel_fe_or_event_design': 8}
- property_rights: {'graduate_to_panel_fe_or_event_design': 8, 'respec_or_counter_hypothesis': 1}
- tax_burden: {'respec_or_counter_hypothesis': 5}
- trade_freedom: {'graduate_to_panel_fe_or_event_design': 3}

## Top Queue Items

- #1 heritage_monetary_freedom_inflation_rate_income_region_robustness | SUPPORTED | q=2.016e-27 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FP.CPI.TOTL.ZG + central-bank-institution proxy
- #2 heritage_government_integrity_private_consumption_pc_income_region_robustness | SUPPORTED | q=3.192e-15 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:CC.EST
- #3 heritage_property_rights_private_consumption_pc_income_region_robustness | SUPPORTED | q=2.52e-08 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #4 heritage_judicial_effectiveness_private_consumption_pc_income_region_robustness | SUPPORTED | q=1.469e-07 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #5 heritage_property_rights_life_expectancy_income_region_robustness | SUPPORTED | q=1.911e-06 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #6 heritage_government_integrity_private_credit_depth_income_region_robustness | SUPPORTED | q=2.033e-05 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:CC.EST
- #7 heritage_government_integrity_life_expectancy_income_region_robustness | SUPPORTED | q=2.959e-05 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:CC.EST
- #8 heritage_judicial_effectiveness_life_expectancy_income_region_robustness | SUPPORTED | q=4.099e-05 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #9 heritage_business_freedom_life_expectancy_income_region_robustness | SUPPORTED | q=4.099e-05 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #10 heritage_economic_freedom_private_consumption_pc_income_region_robustness | SUPPORTED | q=0.0001262 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #11 heritage_judicial_effectiveness_account_ownership_income_region_robustness | SUPPORTED | q=0.0001262 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #12 heritage_property_rights_private_credit_depth_income_region_robustness | SUPPORTED | q=0.0001262 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #13 heritage_economic_freedom_inflation_rate_income_region_robustness | SUPPORTED | q=0.0001547 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #14 heritage_financial_freedom_private_credit_depth_income_region_robustness | SUPPORTED | q=0.0002298 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FS.AST.PRVT.GD.ZS
- #15 heritage_business_freedom_private_credit_depth_income_region_robustness | SUPPORTED | q=0.0003987 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #16 heritage_business_freedom_electricity_access_income_region_robustness | SUPPORTED | q=0.00043 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #17 heritage_business_freedom_inflation_rate_income_region_robustness | SUPPORTED | q=0.0004648 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #18 heritage_business_freedom_under5_mortality_income_region_robustness | SUPPORTED | q=0.000558 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #19 heritage_financial_freedom_private_consumption_pc_income_region_robustness | SUPPORTED | q=0.001176 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FS.AST.PRVT.GD.ZS
- #20 heritage_economic_freedom_high_tech_exports_income_region_robustness | SUPPORTED | q=0.002656 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #21 heritage_financial_freedom_life_expectancy_income_region_robustness | SUPPORTED | q=0.004123 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FS.AST.PRVT.GD.ZS
- #22 heritage_economic_freedom_life_expectancy_income_region_robustness | SUPPORTED | q=0.004179 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #23 heritage_economic_freedom_trade_openness_income_region_robustness | SUPPORTED | q=0.005441 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #24 heritage_economic_freedom_female_lfp_income_region_robustness | SUPPORTED | q=0.005587 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST + wgi:RL.EST + wgi:CC.EST composite
- #25 heritage_monetary_freedom_investment_share_income_region_robustness | SUPPORTED | q=0.006074 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FP.CPI.TOTL.ZG + central-bank-institution proxy
- #26 heritage_trade_freedom_inflation_rate_income_region_robustness | SUPPORTED | q=0.006816 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:NE.TRD.GNFS.ZS / tariff proxy
- #27 heritage_government_integrity_account_ownership_income_region_robustness | SUPPORTED | q=0.007245 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:CC.EST
- #28 heritage_business_freedom_private_consumption_pc_income_region_robustness | SUPPORTED | q=0.0113 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RQ.EST
- #29 heritage_judicial_effectiveness_private_credit_depth_income_region_robustness | SUPPORTED | q=0.0113 | track=graduate_to_panel_fe_or_event_design | proxy=wgi:RL.EST
- #30 heritage_financial_freedom_employment_rate_income_region_robustness | SUPPORTED | q=0.01364 | track=graduate_to_panel_fe_or_event_design | proxy=world_bank_wdi:FS.AST.PRVT.GD.ZS
