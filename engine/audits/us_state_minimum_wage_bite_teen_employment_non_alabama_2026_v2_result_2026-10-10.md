# Non-Alabama ACS teen employment v2 result — 2026-10-10

Registration first commit `cbef14e13d5daf869b1fb5b47adffe1087ac3806` preceded
source lock `9d31f8ec876d6a017c429e1429373e77fe0a5fc0`, which preceded this
run. The 400 exact HTTP response bodies came from the Census Bureau's
`data.census.gov/api/access/data/table` service, one for each frozen
state/year key. Each body is retained, hashed, and checked against table ID,
GEO_ID, underlying ACS one-year Subject Table S2301 API relation, and the
exact `S2301_C03_002E/M` fields. The registered source slice and treatment
vintage are also hash-pinned. The direct `api.census.gov` endpoint was not
used because keyless requests redirect to Missing Key.

**PARTIAL.** All 400 possible pairs from 49 states plus DC are complete;
every state has all eight years. The treatment p90–p10 gap is 0.206791 (floor
0.10). The pre-2019 subset has 250 pairs and 50 states (floors 180 and 40).
The primary fixed-effects coefficient is -5.337856 teen employment percentage
points per one bite-ratio unit, state-clustered SE 2.781004, two-sided
`t(49)` p=0.060767. A +0.10 bite change corresponds to -0.533786 points.
The pre-2019 coefficient is -3.877539, SE 6.383642, p=0.546378. Largest
state residualized-treatment squared share is 0.048593 (ceiling 0.20).
The sign and practical-effect conditions hold, but the primary p value does
not meet the frozen 0.005 threshold. Non-significance is not refutation.

An independent balanced-panel two-way demeaning calculation reproduced the
primary and pre-2019 coefficients to less than 3e-13 and their state-clustered
CR1 standard errors to less than 3e-14. The frozen runner's exact packet
replay also passed.

Alabama was excluded from this separate v2 because its selected estimates
were manually viewed before a source lock during the original 51-state
source-access probe. No other registered state outcome values were opened
before the v2 registration. The original 51-state case remains unrun and
archived; it must not gain public conversion credit from an eventual
same-roster exploratory run. This v2 is a selected, correlated descriptive
calibration, not an independent treatment holdout. It receives no causal,
policy, school-score, or featured credit and does not rescue archived DiD
claims.
