# Steelman - oecd_union_density_disposable_gini_panel

## Claim
In OECD country-years from 1990 to 2022, higher trade-union density is associated with lower disposable-income Gini after country and year fixed effects and unemployment controls.

## Best case
The strongest case for the claim is that unions compress wage schedules, raise worker bargaining power, and help preserve inclusive labour-market norms. Disposable-income Gini is the right hard outcome because it captures both market earnings and tax-transfer systems that unions may politically sustain.

The strongest objection is that union density moves slowly, has measurement breaks, and may be endogenous to deindustrialisation or public-sector size. Country and year fixed effects therefore test only within-country deviations, not the full institutional regime contrast between Nordic and liberal-market systems.

## Pre-analysis guardrails
- Support rule: SUPPORTED iff beta_union_density <= -0.0005 Gini points per 1 pp union density with p<0.10.
- Refutation rule: REFUTED iff beta_union_density >= +0.0005 with p<0.10. PARTIAL otherwise if method-valid.
- Estimator: country and year fixed effects with country-clustered standard errors.
- Identification status: associational; no causal language is licensed by this run alone.
