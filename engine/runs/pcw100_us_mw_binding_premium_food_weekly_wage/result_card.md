# Result card — pcw100_us_mw_binding_premium_food_weekly_wage

- Verdict: **SUPPORTED**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=+0.0104406, SE=0.00210466, p=7.02406e-07, expected_sign=+
- Observations: 561
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 3.05

## Extreme policy groups

- Low-policy units: AL, AR, GA, HI, IA, ID, IN, KS, KY, LA, MD, MS, NC, ND, NE, NH, OK, PA, SC, SD, TN, TX, UT, VA, WI, WV, WY
- High-policy units: AK, AR, AZ, CA, CO, CT, DC, DE, FL, HI, IL, MA, MD, ME, MI, MN, MO, MT, NE, NJ, NM, NV, NY, OH, OR, RI, SD, VA, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.010440576
- Standard error: 0.0021046589
- p-value: 7.0240611e-07
- R-squared: 0.993329
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
