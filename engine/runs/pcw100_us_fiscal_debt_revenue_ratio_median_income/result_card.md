# Result card — pcw100_us_fiscal_debt_revenue_ratio_median_income

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `-`
- Reason: coefficient=-5.23177e-06, SE=0.000302579, p=0.986205, expected_sign=-
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

- Coefficient: -5.2317682e-06
- Standard error: 0.00030257922
- p-value: 0.98620481
- R-squared: 0.991745
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
