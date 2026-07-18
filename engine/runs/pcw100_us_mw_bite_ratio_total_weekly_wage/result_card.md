# Result card — pcw100_us_mw_bite_ratio_total_weekly_wage

- Verdict: **PARTIAL**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=-0.0521366, SE=0.0642879, p=0.417373, expected_sign=+
- Observations: 102
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 0.207684

## Extreme policy groups

- Low-policy units: GA, IA, ID, IN, KS, KY, NC, ND, NH, PA, TN, TX, UT, WI, WY
- High-policy units: AR, AZ, CA, CT, DE, FL, HI, IL, ME, MO, NJ, NM, OR, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.052136622
- Standard error: 0.064287906
- p-value: 0.41737344
- R-squared: 0.999569
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
