# Result card — pcw100_us_fiscal_tax_revenue_share_hpi_growth

- Verdict: **PARTIAL**
- Cohort: `us_fiscal_policy`
- Expected sign: `+`
- Reason: coefficient=-0.0265749, SE=0.0544881, p=0.625749, expected_sign=+
- Observations: 255
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 10.4909

## Extreme policy groups

- Low-policy units: AK, AL, AR, AZ, CO, DE, FL, GA, IA, KY, LA, MO, MS, MT, NH, NM, NV, NY, OH, OK, OR, RI, SC, SD, TN, TX, VT, WI, WV, WY
- High-policy units: CA, CO, CT, DC, DE, FL, GA, HI, IL, IN, KS, MA, MD, ME, MN, NC, ND, NE, NJ, NV, NY, TN, UT, VA, VT, WA, WI

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.026574893
- Standard error: 0.054488073
- p-value: 0.62574857
- R-squared: 0.926116
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
