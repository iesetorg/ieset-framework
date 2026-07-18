# Result card — pcw100_us_fiscal_debt_revenue_ratio_poverty

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `+`
- Reason: coefficient=+0.00178394, SE=0.00632234, p=0.777817, expected_sign=+
- Observations: 255
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 24.3232

## Extreme policy groups

- Low-policy units: AL, AR, AZ, CA, FL, GA, IA, ID, KS, MN, MS, MT, NC, ND, NE, NM, NV, OH, OK, OR, SC, TN, TX, UT, VT, WY
- High-policy units: AK, CO, CT, DC, DE, HI, IL, MA, MD, NH, NJ, NY, RI, SD, VT, WI, WV

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.0017839404
- Standard error: 0.006322342
- p-value: 0.77781739
- R-squared: 0.98253
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
