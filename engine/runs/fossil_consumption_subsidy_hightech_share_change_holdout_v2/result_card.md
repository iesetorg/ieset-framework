# Result card: fossil_consumption_subsidy_hightech_share_change_holdout_v2

Verdict: **PARTIAL**. coefficient did not clear the frozen directional rule.

Historical export-value result: owid_fossil_subsidy_hightech_export_drag_panel (PARTIAL, p=0.224 known).
Preregistration commit: a9a8436192b9ece0df6d746f2303421d26e57b53.
Held-out sample: 247 country-year pairs, 22 countries, zero old-country overlap.
Single-test threshold: two-sided p <= 0.01.
Primary subsidy-per-resident coefficient: +0.0747964; clustered SE 0.277633; p=0.790246.

Technical erratum: the first attempt hit a nullable-year dtype exception before any coefficient was estimated; its artifacts are preserved byte-exact under engine/runs/fossil_consumption_subsidy_hightech_share_change_holdout_v2/attempts/initial_inconclusive. The same year keys are cast to int64 for this replay.
Measured association only; no causal, school, welfare, or policy-score credit.
