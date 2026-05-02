# Steelman - oecd_collective_bargaining_unemployment_nonpenalty

## Claim
In OECD country-years from 1990 to 2022, broader collective-bargaining coverage does not impose a material unemployment penalty.

## Best case
The best pro-coverage argument is coordination: broad bargaining can internalise macro constraints, reduce wage undercutting, and preserve employment by trading wage growth, training, and work-time rules. If this view is right, high coverage should not show a large positive unemployment coefficient once country and year effects absorb institutions and common shocks.

The best skeptical argument is insider-outsider labour economics: broad agreements can price out marginal workers and raise equilibrium unemployment, especially where wage floors are not offset by active labour-market policy.

## Pre-analysis guardrails
- Support rule: SUPPORTED iff the 90% upper confidence bound for beta_bargaining_coverage is <= +0.10 unemployment-rate points per 1 pp coverage.
- Refutation rule: REFUTED iff beta_bargaining_coverage >= +0.10 with p<0.10. PARTIAL otherwise if method-valid.
- Estimator: country and year fixed effects with country-clustered standard errors.
- Identification status: associational; no causal language is licensed by this run alone.
