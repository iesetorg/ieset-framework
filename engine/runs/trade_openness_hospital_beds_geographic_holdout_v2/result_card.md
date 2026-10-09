# Result card: trade_openness_hospital_beds_geographic_holdout_v2

Verdict: **PARTIAL**. estimable association does not clear the nine-test directional decision rule.

Old study: `medical_device_trade_openness_outcomes` (PARTIAL, known at registration).
Preregistration commit: `937d359c699df37fcb94ae6a1424cc9be9449e2d`.
Held-out sample: 1813 lagged pairs, 98 countries, zero countries shared with the old study.
Estimator: country and treatment-year fixed effects with country-clustered standard errors.
Outcome: world_bank_wdi:SH.MED.BEDS.ZS at t+1; trade share at t.
Expected sign: +; two-sided p <= 0.01 across nine related tests.

Primary coefficient: -0.0015363378; clustered SE 0.0021374191; p=0.47227542; 95% CI [-0.0057256023, +0.0026529267].

This result addresses only the measured association, not the older mechanism or a causal policy effect.
