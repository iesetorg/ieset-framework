# Steelman - oecd_collective_bargaining_growth_penalty_kei

## Claim
In OECD annual data from 1990 to 2022, broader collective-bargaining coverage is not associated with a material penalty to real GDP-volume growth.

## Best case
The strongest no-penalty case is that coordinated bargaining can stabilise demand, reduce conflict, and support skill formation, so aggregate growth need not suffer even if wage setting is more collective. The strongest growth-penalty case is that broader coverage slows adjustment, compresses wage dispersion, and reduces employment or investment dynamism. Annual GDP-volume growth is noisy, but it is a direct macro cost metric.

## Pre-analysis guardrails
- Support rule: SUPPORTED iff beta_bargaining_coverage >= -0.02 GDP-growth points per 1 pp coverage OR p>=0.10.
- Refutation rule: REFUTED iff beta_bargaining_coverage <= -0.02 with p<0.10. PARTIAL otherwise if method-valid.
- Estimator: country and year fixed effects with country-clustered standard errors.
- Identification status: associational; no causal language is licensed by this run alone.
