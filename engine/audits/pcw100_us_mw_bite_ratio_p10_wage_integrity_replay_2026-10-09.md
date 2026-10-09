# Minimum-wage bite / p10 screen: independent integrity replay — 2026-10-09

This is a read-only correction review of
`pcw100_us_mw_bite_ratio_p10_wage`. The public disposition remains
`quarantined_pending_v2`; this review does not change its verdict, tier,
school scores, or any original run artifact. It corrects two factual premises
of claim 10 in the July adversarial audit and September remediation.

## Registration and source custody

- The hypothesis and steelman first entered Git in `71888c2c1`; the run first
  entered in its strict descendant `258598d14`. The original spec had an
  associational state/year fixed-effects screen, state-clustered covariance,
  a positive coefficient with two-sided p<0.10 support rule, and explicit
  observation, state, and treatment-contrast gates. The 17 `covers_claims`
  school mappings were added later in `a913dbf95`, after the result was known.
- Both analysis inputs exactly match the run manifest: the USDOL/derived
  minimum-wage treatment panel SHA-256 is `3e2c602b4eafcc922f0166d9cee2be33fc2882a6e5bb80858e55564d36dc2e44`;
  the BLS/derived labor outcome panel SHA-256 is
  `2631b4d7d9cf84b55b2c0b53c91f5a6cbac7181591a27b0f266bcce22e0a0cf3`.
  The USDOL minimum-wage vintage, derived bite vintage, and separate BLS
  OEWS median and p10 wage vintages also match their recorded hashes.
- Of 13 files enumerated by the two June build manifests and the May bite
  manifest, 12 current files match their recorded SHA-256 values. The tracked
  state spine changed in September: the current
  file hashes to `8cc434e7a439c7e36d3b884733d8a59b4c350ddf3cdac22d3300a9376a4322bf`,
  while the June build manifest pins
  `2d353eff30c0661abfc09cbe8d711f2ac1f23022e3ec49f7ed9b064c18ed93ac`.
  The exact older bytes remain in Git at
  `f3508d602:data/derived/state_universe_admin1.parquet`. The two derived
  analysis inputs themselves still match the run and were used in the replay.

## Row-level and result checks

- The analysis has 459 unique state-year rows from 51 jurisdictions and nine
  observed years (2014–2018, 2020–2021, 2023–2024). The bottom/top treatment
  cutoffs are 0.4091433849 and 0.5050791685. Each quartile has 115 **rows**;
  their state-year key intersection is empty. HI, MA, MD, MS, and NY appear
  in both displayed state-name lists because different years enter different
  quartiles. The overlapping names do not establish a contrast pipeline bug.
- The treatment is the effective legal minimum wage divided by the BLS median
  hourly wage in all 459 analytic rows. The outcome is the separately sourced
  BLS tenth-percentile wage, log transformed. It is not the denominator in
  any analytic row. Among 115 top-quartile rows, no p10 wage equals the legal
  floor exactly; two are one cent above it and the other 113 are farther above.
  The original audit's literal assertion that the p10 wage *is* the minimum
  wage in high-bite states is false. Full-model R²=0.974915 includes state and
  year effects; the effects-only R² is 0.959524, so the full R² does not
  establish a mechanical identity.
- The registered runner was executed into a temporary directory, leaving the
  original run untouched. Its coefficient Parquet, chart data, replication
  script, and original pre-correction result card match byte for byte. The
  diagnostic and manifest values match after removing only the new timestamp
  and later correction; the run's frozen hypothesis matches after excluding
  the 17 later school mappings. The estimate remains +0.5883855769,
  state-clustered SE 0.0860611951, two-sided p=8.0965928468e-12,
  459 rows, 51 states, and the original directional `SUPPORTED` verdict.

## Decision boundary

The stored coefficient supports the **registered descriptive association**.
Same-year wage distribution measures appear in both the treatment denominator
and outcome, and wage-floor policy can respond to local wage conditions. That
endogeneity and source-family coupling prevent a causal wage-effect claim.
The 17 mappings added after the result must receive **zero automatic school
score credit** if the run becomes publicly visible as calibration. A
calibration-only rescope is defensible after correcting the July/September
audit language and enforcing that zero-score gate; the old `SUPPORTED` label
must remain visibly scoped to the associational screen. Until those changes
are reviewed and applied together, keep the quarantine and count no new
graduation from this case. A causal claim needs a separately registered event
design with a distinct outcome window and independent holdout.
