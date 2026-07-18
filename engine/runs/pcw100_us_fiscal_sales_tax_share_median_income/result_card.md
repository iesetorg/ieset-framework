# Result card — pcw100_us_fiscal_sales_tax_share_median_income

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `-`
- Reason: coefficient=-0.000214443, SE=0.000899834, p=0.811637, expected_sign=-
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

- Coefficient: -0.00021444322
- Standard error: 0.00089983408
- p-value: 0.81163742
- R-squared: 0.991748
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
