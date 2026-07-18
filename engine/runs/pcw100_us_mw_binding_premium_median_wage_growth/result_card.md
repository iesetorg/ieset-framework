# Result card — pcw100_us_mw_binding_premium_median_wage_growth

- Verdict: **PARTIAL**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=-0.0144731, SE=0.11402, p=0.898992, expected_sign=+
- Observations: 306
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 2.715

## Extreme policy groups

- Low-policy units: AL, GA, IA, ID, IN, KS, KY, LA, MS, NC, ND, NH, OK, PA, SC, TN, TX, UT, VA, WI, WY
- High-policy units: AK, AR, AZ, CA, CO, CT, DC, DE, FL, HI, IL, MA, MD, ME, MI, MN, MO, MT, NE, NJ, NM, NV, NY, OH, OR, RI, SD, VA, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.014473072
- Standard error: 0.11401974
- p-value: 0.898992
- R-squared: 0.312735
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
