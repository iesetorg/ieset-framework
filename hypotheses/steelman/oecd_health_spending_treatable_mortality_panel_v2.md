# Steelman — oecd_health_spending_treatable_mortality_panel_v2

**Measured claim.** Among the 42 fixed country codes, a higher OECD public health-programme spending share of GDP in year t is associated with a lower OECD treatable-death rate per 100,000 people at exact year t+1, conditional on real income per person, unemployment, and country and year effects.

**Strong rival explanation.** Ageing, medical innovation, disease mix, and income can move spending and mortality together. Extra public spending may compensate for severe disease burden, yielding reverse causation. The test is a measured association only; a lower rate does not identify a spending effect.

**Decision rule.** Return INCONCLUSIVE if fewer than 150 complete country-year pairs or 20 countries survive the four-treatment-year-per-country rule, or if the frozen primary country/year fixed-effects estimator or country-clustered t uncertainty is unidentified/nonfinite. Otherwise SUPPORT requires a negative coefficient at two-sided p<=0.025; REFUTATION requires a positive coefficient at the same cutoff. Every other estimable result is PARTIAL. All four registered tests remain in the Bonferroni family even if one is inconclusive.

**Evidence boundary.** Four-test family; the old REFUTED proxy result for `public_health_spending_avoidable_mortality_panel` is known, and this is not a geographic or temporal holdout from that result. Numeric availability masks were inspected before registration, without outcome magnitudes, signs, or fits. Category-to-outcome associations may be confounded and cannot establish a programme effect. No causal, policy, or school-score credit.
