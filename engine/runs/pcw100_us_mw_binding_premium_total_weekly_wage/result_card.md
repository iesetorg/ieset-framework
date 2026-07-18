# Result card — pcw100_us_mw_binding_premium_total_weekly_wage

- Verdict: **PARTIAL**
- Cohort: `us_minimum_wage`
- Expected sign: `+`
- Reason: coefficient=-0.00146064, SE=0.0025661, p=0.569217, expected_sign=+
- Observations: 102
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 6.415

## Extreme policy groups

- Low-policy units: AL, GA, IA, ID, IN, KS, KY, LA, MS, NC, ND, NH, OK, PA, SC, TN, TX, UT, WI, WY
- High-policy units: AZ, CA, CO, CT, DC, HI, IL, MA, MD, ME, NJ, NY, OR, RI, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: -0.0014606371
- Standard error: 0.0025660972
- p-value: 0.56921657
- R-squared: 0.999564
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
