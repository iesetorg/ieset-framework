# Result card — pcw100_us_mw_binding_premium_poverty

- Verdict: **PARTIAL**
- Cohort: `us_minimum_wage`
- Expected sign: `-`
- Reason: coefficient=+0.0424089, SE=0.0598345, p=0.478467, expected_sign=-
- Observations: 255
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 3.75

## Extreme policy groups

- Low-policy units: AL, GA, IA, ID, IN, KS, KY, LA, MS, NC, ND, NH, OK, PA, SC, TN, TX, UT, VA, WI, WY
- High-policy units: AR, AZ, CA, CO, CT, DC, HI, IL, MA, MD, ME, MO, NJ, NM, NY, OR, RI, VA, VT, WA

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +0.042408868
- Standard error: 0.059834468
- p-value: 0.4784673
- R-squared: 0.982592
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
