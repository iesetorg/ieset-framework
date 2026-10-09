# Result card: wdi_business_entry_rule_of_law_geographic_holdout_v2

Verdict: **PARTIAL**. estimable holdout result does not clear support or refutation gates.

## Registered design

This tests the original business-entry by rule-of-law association in countries
outside the old 60-country sample. The old positive result was known at the
time of this follow-up registration. This is an associational geographic
holdout, not a causal policy effect.

- Registration commit: `3e2909666fdb37cb17a1394f4a336c1398c7c0d0`
- Treatment years: 2006–2019
- Sample: 1234 country-years across 109 countries
- Old-sample country overlap: 0
- Estimator: OLS country/year FE with country-clustered standard errors
- Outcome: mean real GDP-per-capita growth in exact calendar years t+1 through t+3

## Primary result

- Interaction coefficient: +0.3522 (clustered SE 0.3436; p=0.3054)
- 95% confidence interval: [-0.3212, +1.0255]
- Rule-of-law p25/p75: -0.747 / +0.374
- Implied entry-slope gap at rule-of-law p75 versus p25: +0.3948

## Interpretation and limits

The frozen thresholds and data gate are in the spec. Business registrations
may reflect filing reforms or formalization rather than productive entry.
Rule of law and growth share potential time-varying confounders. No school
score or public claim is changed by this run alone.
