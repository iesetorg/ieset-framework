# BLOCKED — second_generation_education_outcomes_by_origin

**Status:** blocked at v1 wiring stage.

## Reason

The pre-registered estimator is a **student-level pooled regression** on OECD PISA microdata (waves 2003, 2006, 2009, 2012, 2015, 2018, 2022) with student-level covariates (immigrant generation, home language, parental ESCS, parental education ISCED) and destination-country × origin-region interactions. PISA microdata is not present in `data/vintages/`. There is no OECD PISA fetcher wired in the current run-bootstrap manifest.

All five `decomposition_channels` (parental ESCS, language-of-instruction, parental education, origin-region education norms, years-since-arrival) are PISA student-level variables and are not available from country-aggregate vintages.

## Path to unblock

1. Wire an OECD PISA microdata fetcher (public-use files via OECD data portal) — outputs at student-level granularity.
2. Optionally add Barro-Lee education attainment vintages for origin-region education norms (the one channel that can be approximated from country-aggregate sources).

Pre-registration is preserved. The hypothesis cannot be tested at the spec's required granularity using country-year aggregate data — coarsening to country-level PISA mean scores would silently change the hypothesis being tested.
