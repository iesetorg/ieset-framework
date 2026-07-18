# Result card — pcw100_us_mw_bite_ratio_median_wage_growth

- Verdict: **REFUTED**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=-6.54003, SE=2.95181, p=0.0267191, expected_sign=+
- Observations: 306
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 0.0918064

## Extreme policy groups

- Low-policy units: AK, AL, DC, DE, GA, IA, ID, IN, KS, KY, LA, MA, MD, MS, NC, ND, NH, NJ, OK, PA, SC, TN, TX, UT, VA, WI, WY
- High-policy units: AR, AZ, CA, CO, CT, DE, FL, HI, IL, MD, ME, MI, MO, MS, MT, NE, NJ, NM, NV, NY, OR, RI, SD, VT, WA, WV

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -6.5400295
- Standard error: 2.9518131
- p-value: 0.026719082
- R-squared: 0.331496
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
