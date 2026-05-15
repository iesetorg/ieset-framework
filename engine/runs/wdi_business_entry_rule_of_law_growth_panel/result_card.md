# Result Card - wdi_business_entry_rule_of_law_growth_panel

Verdict: **SUPPORTED** (positive interaction clears p-value, magnitude, and coverage gates).

## Design

- Claim: business-entry intensity predicts stronger three-year forward GDP-per-capita growth mainly where WGI rule of law is higher.
- Data: local WDI new business registrations, population, GDP-per-capita growth, and WGI rule-of-law vintages listed in `manifest.yaml`.
- Sample: 711 country-years, 59 countries, 2006-2019 after forward-outcome construction.
- Estimator: OLS panel FE with country and year fixed effects, clustered by country.

## Primary Result

- Interaction coefficient: 0.498
- Clustered p-value: 0.025
- 95% CI: [0.063, 0.934]
- Model-implied marginal entry effect at rule-of-law p25 (-0.373): -0.714
- Model-implied marginal entry effect at rule-of-law p75 (1.419): 0.179
- P75-minus-p25 marginal gap: 0.893

## Caveats

This is an associational screen. Business-registration counts can move because of filing reforms, formalisation drives, tax incentives, or shell-firm behavior. The result should not be scored as causal evidence without a richer design.
