# Steelman - oecd_youth_wage_gap_youth_employment

## Claim
In OECD country-years from 1990 to 2022, a wider youth-to-prime-age wage gap is associated with lower youth employment, even after controlling for the aggregate unemployment rate.

## Best case
The strongest interpretation is a segmentation story: when youth wages lag prime-age wages more sharply, young workers may be in weaker positions and youth employment ratios should also be lower. The strongest objection is reverse causality and composition: low youth employment may itself select which youths remain employed and alter the measured wage gap.

## Pre-analysis guardrails
- Support rule: SUPPORTED iff beta_youth_prime_wage_gap <= -0.20 youth-employment-ratio points per 1 pp wage gap with p<0.10.
- Refutation rule: REFUTED iff beta_youth_prime_wage_gap >= 0 with p<0.10. PARTIAL otherwise if method-valid.
- Estimator: country and year fixed effects with country-clustered standard errors.
- Identification status: associational; no causal language is licensed by this run alone.
