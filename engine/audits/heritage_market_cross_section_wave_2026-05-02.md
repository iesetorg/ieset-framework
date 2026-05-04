# Heritage Market-Order Cross-Section Wave - 2026-05-02

## What was tested

- Generated 192 candidate hypotheses: 12 Heritage Index of Economic Freedom pillars x 16 WDI outcomes.
- Treatment contrast: top quartile vs bottom quartile of countries on the 2024 Heritage pillar score.
- Outcome window: latest available WDI country observation from 2018-2024.
- Sample base: 183 countries in the cleaned Heritage 2024 panel; each test drops missing WDI outcome observations.
- Estimator: Welch mean contrast. This is descriptive/associational triage, not a causal policy-effect design.

## Verdict counts

- SUPPORTED: 138
- PARTIAL: 35
- REFUTED: 19
- INCONCLUSIVE_DATA_PENDING: 0
- BH/FDR q<=0.10 among finite Welch tests: {'SUPPORTED': 134, 'REFUTED': 19}

## Pillar-level pattern

- overall_score: S=14, P=2, R=0, I=0
- property_rights: S=15, P=1, R=0, I=0
- judicial_effectiveness: S=15, P=1, R=0, I=0
- government_integrity: S=14, P=2, R=0, I=0
- tax_burden: S=0, P=10, R=6, I=0
- government_spending: S=0, P=3, R=13, I=0
- business_freedom: S=13, P=3, R=0, I=0
- labor_freedom: S=14, P=2, R=0, I=0
- monetary_freedom: S=12, P=4, R=0, I=0
- trade_freedom: S=14, P=2, R=0, I=0
- investment_freedom: S=13, P=3, R=0, I=0
- financial_freedom: S=14, P=2, R=0, I=0

## Outcome-level pattern

- account_ownership: S=10, P=0, R=2, I=0
- electricity_access: S=10, P=1, R=1, I=0
- employment_rate: S=3, P=9, R=0, I=0
- extreme_poverty: S=10, P=1, R=1, I=0
- female_lfp: S=7, P=4, R=1, I=0
- gdp_pc_ppp: S=10, P=1, R=1, I=0
- high_tech_exports: S=10, P=0, R=2, I=0
- inflation_rate: S=9, P=2, R=1, I=0
- investment_share: S=0, P=12, R=0, I=0
- life_expectancy: S=10, P=1, R=1, I=0
- physician_density: S=9, P=2, R=1, I=0
- private_consumption_pc: S=10, P=0, R=2, I=0
- private_credit_depth: S=10, P=0, R=2, I=0
- tertiary_enrollment: S=10, P=0, R=2, I=0
- trade_openness: S=10, P=1, R=1, I=0
- under5_mortality: S=10, P=1, R=1, I=0

## Strongest nominal supports

- heritage_business_freedom_life_expectancy_current_gap: p=1.912e-25, q=3.671e-23, diff=15.29, n_high=44, n_low=44
- heritage_business_freedom_tertiary_enrollment_current_gap: p=1.302e-21, q=1.25e-19, diff=59.77, n_high=37, n_low=36
- heritage_government_integrity_life_expectancy_current_gap: p=3.397e-19, q=2.174e-17, diff=12.08, n_high=45, n_low=45
- heritage_judicial_effectiveness_account_ownership_current_gap: p=9.213e-18, q=4.422e-16, diff=47.22, n_high=36, n_low=36
- heritage_business_freedom_gdp_pc_ppp_current_gap: p=1.35e-17, q=5.184e-16, diff=5.208e+04, n_high=43, n_low=43
- heritage_business_freedom_account_ownership_current_gap: p=1.952e-17, q=5.193e-16, diff=46.37, n_high=35, n_low=34
- heritage_trade_freedom_physician_density_current_gap: p=2.001e-17, q=5.193e-16, diff=2.841, n_high=47, n_low=42
- heritage_property_rights_life_expectancy_current_gap: p=2.349e-17, q=5.193e-16, diff=12.01, n_high=45, n_low=45
- heritage_labor_freedom_account_ownership_current_gap: p=2.681e-17, q=5.193e-16, diff=38.74, n_high=35, n_low=34
- heritage_government_integrity_account_ownership_current_gap: p=2.705e-17, q=5.193e-16, diff=46.9, n_high=36, n_low=36
- heritage_business_freedom_physician_density_current_gap: p=3.047e-17, q=5.319e-16, diff=3.152, n_high=42, n_low=42
- heritage_government_integrity_physician_density_current_gap: p=4.447e-17, q=7.114e-16, diff=2.788, n_high=43, n_low=43
- heritage_judicial_effectiveness_life_expectancy_current_gap: p=1.773e-16, q=2.619e-15, diff=10.81, n_high=45, n_low=45
- heritage_trade_freedom_life_expectancy_current_gap: p=3.637e-16, q=4.987e-15, diff=11.2, n_high=51, n_low=44
- heritage_business_freedom_under5_mortality_current_gap: p=4.45e-16, q=5.696e-15, diff=-49.11, n_high=44, n_low=44

## Strongest nominal refutations

- heritage_government_spending_life_expectancy_current_gap: p=2.308e-13, q=1.528e-12, diff=-11.25, n_high=44, n_low=44
- heritage_government_spending_physician_density_current_gap: p=2.48e-13, q=1.587e-12, diff=-2.773, n_high=42, n_low=42
- heritage_government_spending_account_ownership_current_gap: p=8.136e-13, q=4.222e-12, diff=-39.57, n_high=34, n_low=34
- heritage_government_spending_under5_mortality_current_gap: p=2.256e-11, q=8.664e-11, diff=38.02, n_high=44, n_low=44
- heritage_government_spending_private_consumption_pc_current_gap: p=1.231e-09, q=3.692e-09, diff=-1.3e+04, n_high=37, n_low=37
- heritage_government_spending_gdp_pc_ppp_current_gap: p=3.227e-09, q=9.248e-09, diff=-3.289e+04, n_high=43, n_low=43
- heritage_government_spending_tertiary_enrollment_current_gap: p=9.693e-09, q=2.585e-08, diff=-41.12, n_high=36, n_low=36
- heritage_government_spending_electricity_access_current_gap: p=9.142e-08, q=2.141e-07, diff=-27.28, n_high=44, n_low=44
- heritage_government_spending_private_credit_depth_current_gap: p=7.064e-07, q=1.507e-06, diff=-43.22, n_high=38, n_low=38
- heritage_government_spending_extreme_poverty_current_gap: p=2.091e-06, q=4.271e-06, diff=25.24, n_high=32, n_low=32
- heritage_tax_burden_account_ownership_current_gap: p=2.887e-05, q=5.331e-05, diff=-20.97, n_high=35, n_low=35
- heritage_tax_burden_private_consumption_pc_current_gap: p=0.0001134, q=0.000198, diff=-8987, n_high=38, n_low=38
- heritage_government_spending_trade_openness_current_gap: p=0.0008018, q=0.001272, diff=-46.21, n_high=39, n_low=39
- heritage_tax_burden_private_credit_depth_current_gap: p=0.003502, q=0.005253, diff=-28.86, n_high=38, n_low=38
- heritage_tax_burden_high_tech_exports_current_gap: p=0.009281, q=0.01304, diff=-6.701, n_high=41, n_low=41

## Interpretation

- The evidence is strongest for ordoliberal/Austrian-compatible market-order pillars: property rights, judicial effectiveness, government integrity, business freedom, trade freedom, investment freedom, financial freedom, and monetary freedom.
- The fiscal-size simplification is not rescued by this wave: tax-burden and especially government-spending scores produce multiple refutations, meaning richer/high-QOL countries often have larger fiscal states or heavier tax systems.
- The cleanest next graduation path is to convert the strongest supported pillars into panel/event specs with controls for income, region, resource rents, and baseline state capacity.
- These runs should be published as exploratory result cards only until a robustness wave is done; they are legitimate hypothesis/data/test artifacts, not final causal wins.
