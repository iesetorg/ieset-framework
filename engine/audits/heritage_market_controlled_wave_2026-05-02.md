# Heritage Market-Order Controlled Robustness Wave - 2026-05-02

## What was tested

- Generated 180 controlled candidate hypotheses: 12 Heritage IEF pillars x 15 non-GDP WDI outcomes.
- Design: cross-sectional OLS of latest outcome on standardized 2024 Heritage pillar score, log real GDP per capita PPP, and Heritage region fixed effects.
- Outcome/control window: latest available country observations from 2018-2024.
- This is a stricter descriptive robustness screen, not a causal design.
- Baseline comparison: First wave was 138 SUPPORTED, 35 PARTIAL, 19 REFUTED, 0 INCONCLUSIVE.

## Verdict counts

- SUPPORTED: 75
- PARTIAL: 89
- REFUTED: 16
- INCONCLUSIVE_DATA_PENDING: 0
- BH/FDR q<=0.10 among finite controlled tests: {'SUPPORTED': 59, 'REFUTED': 14}

## Pillar-level pattern

- overall_score: S=9, P=6, R=0, I=0
- property_rights: S=9, P=5, R=1, I=0
- judicial_effectiveness: S=9, P=5, R=1, I=0
- government_integrity: S=10, P=4, R=1, I=0
- tax_burden: S=1, P=8, R=6, I=0
- government_spending: S=0, P=9, R=6, I=0
- business_freedom: S=9, P=6, R=0, I=0
- labor_freedom: S=3, P=12, R=0, I=0
- monetary_freedom: S=6, P=9, R=0, I=0
- trade_freedom: S=8, P=7, R=0, I=0
- investment_freedom: S=5, P=10, R=0, I=0
- financial_freedom: S=6, P=8, R=1, I=0

## Outcome-level pattern

- account_ownership: S=5, P=5, R=2, I=0
- electricity_access: S=1, P=11, R=0, I=0
- employment_rate: S=6, P=6, R=0, I=0
- extreme_poverty: S=0, P=8, R=4, I=0
- female_lfp: S=7, P=5, R=0, I=0
- high_tech_exports: S=5, P=6, R=1, I=0
- inflation_rate: S=7, P=5, R=0, I=0
- investment_share: S=1, P=11, R=0, I=0
- life_expectancy: S=8, P=2, R=2, I=0
- physician_density: S=3, P=8, R=1, I=0
- private_consumption_pc: S=8, P=2, R=2, I=0
- private_credit_depth: S=9, P=1, R=2, I=0
- tertiary_enrollment: S=5, P=5, R=2, I=0
- trade_openness: S=5, P=7, R=0, I=0
- under5_mortality: S=5, P=7, R=0, I=0

## Strongest controlled supports

- heritage_monetary_freedom_inflation_rate_income_region_robustness: p=1.12e-29, q=2.016e-27, coef=-16.85, n=167
- heritage_government_integrity_private_consumption_pc_income_region_robustness: p=3.547e-17, q=3.192e-15, coef=5798, n=150
- heritage_property_rights_private_consumption_pc_income_region_robustness: p=4.2e-10, q=2.52e-08, coef=4634, n=150
- heritage_judicial_effectiveness_private_consumption_pc_income_region_robustness: p=3.265e-09, q=1.469e-07, coef=3967, n=150
- heritage_property_rights_life_expectancy_income_region_robustness: p=5.307e-08, q=1.911e-06, coef=1.895, n=174
- heritage_government_integrity_private_credit_depth_income_region_robustness: p=7.904e-07, q=2.033e-05, coef=17.87, n=155
- heritage_government_integrity_life_expectancy_income_region_robustness: p=1.315e-06, q=2.959e-05, coef=1.632, n=174
- heritage_judicial_effectiveness_life_expectancy_income_region_robustness: p=2.103e-06, q=4.099e-05, coef=1.489, n=174
- heritage_business_freedom_life_expectancy_income_region_robustness: p=2.277e-06, q=4.099e-05, coef=2.285, n=170
- heritage_economic_freedom_private_consumption_pc_income_region_robustness: p=7.864e-06, q=0.0001262, coef=3513, n=147
- heritage_judicial_effectiveness_account_ownership_income_region_robustness: p=9.111e-06, q=0.0001262, coef=7.308, n=139
- heritage_property_rights_private_credit_depth_income_region_robustness: p=9.117e-06, q=0.0001262, coef=16.96, n=155
- heritage_economic_freedom_inflation_rate_income_region_robustness: p=1.203e-05, q=0.0001547, coef=-11.4, n=167
- heritage_financial_freedom_private_credit_depth_income_region_robustness: p=1.915e-05, q=0.0002298, coef=14.48, n=151
- heritage_business_freedom_private_credit_depth_income_region_robustness: p=3.544e-05, q=0.0003987, coef=22.49, n=151
- heritage_business_freedom_electricity_access_income_region_robustness: p=4.061e-05, q=0.00043, coef=7.985, n=169
- heritage_business_freedom_inflation_rate_income_region_robustness: p=4.648e-05, q=0.0004648, coef=-14.54, n=167
- heritage_business_freedom_under5_mortality_income_region_robustness: p=5.89e-05, q=0.000558, coef=-8.218, n=170
- heritage_financial_freedom_private_consumption_pc_income_region_robustness: p=0.0001437, q=0.001176, coef=2608, n=147
- heritage_economic_freedom_high_tech_exports_income_region_robustness: p=0.0003393, q=0.002656, coef=5.143, n=159

## Strongest controlled refutations

- heritage_tax_burden_private_consumption_pc_income_region_robustness: p=1.506e-07, q=4.518e-06, coef=-2697, n=148
- heritage_tax_burden_private_credit_depth_income_region_robustness: p=6.613e-05, q=0.0005952, coef=-10.92, n=152
- heritage_government_spending_account_ownership_income_region_robustness: p=8.658e-05, q=0.0007421, coef=-5.943, n=135
- heritage_government_spending_private_consumption_pc_income_region_robustness: p=0.0005494, q=0.003983, coef=-2232, n=147
- heritage_tax_burden_life_expectancy_income_region_robustness: p=0.0005532, q=0.003983, coef=-0.8944, n=171
- heritage_tax_burden_tertiary_enrollment_income_region_robustness: p=0.004933, q=0.01936, coef=-5.167, n=141
- heritage_financial_freedom_extreme_poverty_income_region_robustness: p=0.009612, q=0.03327, coef=3.3, n=127
- heritage_tax_burden_account_ownership_income_region_robustness: p=0.01161, q=0.0387, coef=-2.983, n=136
- heritage_judicial_effectiveness_extreme_poverty_income_region_robustness: p=0.01413, q=0.04463, coef=3.345, n=129
- heritage_government_spending_tertiary_enrollment_income_region_robustness: p=0.01484, q=0.04606, coef=-5.231, n=141
- heritage_government_spending_private_credit_depth_income_region_robustness: p=0.01595, q=0.04785, coef=-8.017, n=151
- heritage_government_spending_life_expectancy_income_region_robustness: p=0.02111, q=0.0589, coef=-0.6981, n=170
- heritage_property_rights_extreme_poverty_income_region_robustness: p=0.02749, q=0.0717, coef=3.264, n=129
- heritage_government_integrity_extreme_poverty_income_region_robustness: p=0.03691, q=0.09222, coef=3.076, n=129
- heritage_tax_burden_high_tech_exports_income_region_robustness: p=0.0414, q=0.1007, coef=-2.012, n=160
- heritage_government_spending_physician_density_income_region_robustness: p=0.05096, q=0.1207, coef=-0.1814, n=163

## Interpretation

- The first-wave signal substantially survives but is disciplined: 75 controlled supports remain, while 89 become partial after income and region controls.
- The durable pro-market cluster is now narrower and more credible: private consumption above income, life expectancy, private-credit depth, inflation discipline, female LFP/employment in several pillars, and high-tech exports in selected legal/business pillars.
- The clean ordoliberal result is stronger than the crude Austrian-fiscal one: legal/order/competition/business/monetary pillars survive better than low-tax or low-spending pillars.
- Fiscal-size absolutism remains actively harmed by the evidence: tax-burden and government-spending scores account for most controlled refutations.
- Next graduation target: convert the strongest controlled supports into panel specs using WGI/IEF-style time-varying proxies plus country/year fixed effects, and separately register fiscal-state-size hypotheses that allow welfare-state complementarity rather than assuming smaller is always better.
