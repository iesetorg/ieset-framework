# Result card — pcw100_us_mw_binding_premium_p10_wage

- Verdict: **SUPPORTED**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=+0.0240881, SE=0.00331536, p=3.71379e-13, expected_sign=+
- Observations: 459
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 2.79

## Extreme policy groups

- Low-policy units: AL, AR, GA, HI, IA, ID, IN, KS, KY, LA, MD, MS, NC, ND, NE, NH, OK, PA, SC, SD, TN, TX, UT, VA, WI, WV, WY
- High-policy units: AK, AR, AZ, CA, CO, CT, DC, DE, FL, HI, IL, MA, MD, ME, MI, MN, MO, MT, NE, NJ, NM, NV, NY, OH, OR, RI, SD, VA, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.024088079
- Standard error: 0.0033153588
- p-value: 3.713793e-13
- R-squared: 0.975473
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
