# Result card — pcw100_us_fiscal_sales_tax_share_permit_units

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `-`
- Reason: coefficient=-0.00818132, SE=0.00979508, p=0.403578, expected_sign=-
- Observations: 255
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 6.7329

## Extreme policy groups

- Low-policy units: AK, AR, CA, CO, DC, DE, GA, IA, LA, MA, MN, MO, MT, ND, NH, NM, NY, OK, OR, RI, SC, VA, VT, WI, WV, WY
- High-policy units: AZ, CT, FL, HI, ID, IL, IN, KS, ME, MN, MS, NE, NJ, NV, OH, PA, SD, TN, TX, WA, WI

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.0081813155
- Standard error: 0.0097950771
- p-value: 0.40357826
- R-squared: 0.990332
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
