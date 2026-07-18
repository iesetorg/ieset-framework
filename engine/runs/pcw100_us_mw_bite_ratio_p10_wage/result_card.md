# Result card — pcw100_us_mw_bite_ratio_p10_wage

- Verdict: **SUPPORTED**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=+0.588386, SE=0.0860612, p=8.09659e-12, expected_sign=+
- Observations: 459
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 0.0959358

## Extreme policy groups

- Low-policy units: AK, AL, DC, GA, HI, IA, ID, IN, KS, KY, LA, MA, MD, MS, NC, ND, NH, NY, OK, PA, SC, TN, TX, UT, VA, WI, WY
- High-policy units: AR, AZ, CA, CO, CT, DE, FL, HI, IL, MA, MD, ME, MI, MO, MS, MT, NE, NJ, NM, NV, NY, OR, RI, SD, VT, WA, WV

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.58838558
- Standard error: 0.086061195
- p-value: 8.0965928e-12
- R-squared: 0.974915
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
