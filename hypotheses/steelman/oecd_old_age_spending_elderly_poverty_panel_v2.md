# Steelman — oecd_old_age_spending_elderly_poverty_panel_v2

**Measured claim.** Among the 42 fixed country codes, a higher OECD public old-age-programme spending share of GDP in year t is associated with a lower over-65 relative-poverty rate at exact year t+1, conditional on real income per person, unemployment, and country and year effects.

**Strong rival explanation.** Population ageing can increase programme outlays while changing the composition of the over-65 poverty denominator. The spending category includes care services; it is not a pension-benefit rate. A negative association may reflect broad redistribution or economic conditions.

**Decision rule.** Return INCONCLUSIVE if fewer than 150 complete country-year pairs or 20 countries survive the four-treatment-year-per-country rule, or if the frozen primary country/year fixed-effects estimator or country-clustered t uncertainty is unidentified/nonfinite. Otherwise SUPPORT requires a negative coefficient at two-sided p<=0.025; REFUTATION requires a positive coefficient at the same cutoff. Every other estimable result is PARTIAL. All four registered tests remain in the Bonferroni family even if one is inconclusive.

**Evidence boundary.** Four-test family; the old PARTIAL proxy result for `public_pension_generosity_elderly_poverty_fiscal_tradeoff` is known, and this is not a geographic or temporal holdout from that result. Numeric availability masks were inspected before registration, without outcome magnitudes, signs, or fits. Category-to-outcome associations may be confounded and cannot establish a programme effect. No causal, policy, or school-score credit.
