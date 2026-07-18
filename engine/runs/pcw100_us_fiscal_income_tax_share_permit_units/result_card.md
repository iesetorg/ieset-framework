# Result card — pcw100_us_fiscal_income_tax_share_permit_units

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `-`
- Reason: coefficient=-0.00685338, SE=0.0066531, p=0.302961, expected_sign=-
- Observations: 220
- Units: 44
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 6.97798

## Extreme policy groups

- Low-policy units: AL, AR, AZ, IA, KS, KY, LA, MS, ND, NH, NM, OH, OK, PA, RI, TN, VT, WV
- High-policy units: CA, CO, CT, GA, IL, MA, MD, MN, NC, NE, NJ, NY, OR, UT, VA, WI

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.0068533825
- Standard error: 0.0066531016
- p-value: 0.30296147
- R-squared: 0.99119
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
