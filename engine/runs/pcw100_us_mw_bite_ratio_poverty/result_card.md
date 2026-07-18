# Result card — pcw100_us_mw_bite_ratio_poverty

- Verdict: **PARTIAL**
- Cohort: `us_minimum_wage`
- Expected sign: `-`
- Reason: coefficient=+1.39907, SE=2.12192, p=0.509676, expected_sign=-
- Observations: 153
- Units: 51
- Contrast: bottom treatment quartile versus top treatment quartile
- Contrast gap: 0.101514

## Extreme policy groups

- Low-policy units: DC, GA, IA, ID, IN, KS, KY, NC, ND, NH, OK, PA, TN, TX, UT, VA, WI, WY
- High-policy units: AR, AZ, CA, CO, CT, FL, MD, ME, MI, MO, NJ, NM, NV, NY, OR, RI, SD, VT, WA, WV

## Registered decision rule

Expected-sign coefficient with two-sided p<0.10 is SUPPORTED; significant opposite sign is REFUTED; all other estimable results are PARTIAL. A failed data gate is INCONCLUSIVE.

## Interpretation

This result is an associational screen. Fixed effects, temporal ordering, or baseline controls narrow some rival explanations but do not establish causality.

## Estimate

- Coefficient: +1.3990723
- Standard error: 2.1219231
- p-value: 0.50967639
- R-squared: 0.98746
- Method: statsmodels OLS with state/year indicators and state-clustered covariance
