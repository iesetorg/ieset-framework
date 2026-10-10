# Distinct ACS teen employment preregistration — non-Alabama v2

The original 51-jurisdiction registration remains unrun and archived. During
its official-source access audit, the analyst manually viewed Alabama's
`S2301_C03_002E` estimates for all eight selected years and its 2024 margin
of error before a source lock. This new registration excludes Alabama for that
specific disclosed reason, **before opening any selected employment values
for the remaining 49 states plus DC**. It does not describe those 50 units as
an independent treatment holdout: the wage-bite source and related IESET
questions have already been screened.

The committed roster is 400 exact state/year keys, eight nonconsecutive years
(2014–2018, 2021, 2023–2024), with territories, 2019, 2020, and 2022 omitted
for the previously specified reasons. The treatment is the same hash-pinned
2026-05-14 minimum-wage/median-wage ratio vintage. The outcome is the exact
Census ACS one-year Subject Table S2301 age-16–19 employment/population
estimate `S2301_C03_002E`; `S2301_C03_002M` is retained as uncertainty
metadata. The registered source transport is the Census Bureau's public
`https://data.census.gov/api/access/data/table` service, queried for each
key with `id=ACSST1Y{year}.S2301&g=040XX00US{state_fips}`. Preserve each
unmodified response body and hash. Validate the returned `objectId`, `GEO_ID`,
`dataAPIURI`, exact variable headers, and one state row before constructing
the selected source slice. The direct `api.census.gov` endpoint currently
redirects keyless requests to Missing Key; it is not the retrieval URL for
this v2.

The state/year fixed-effects estimator, state-clustered inference, coverage
and contrast floors, pre-2019 sign check, concentration ceiling, two-sided
`p<=0.005`, and ±0.5 percentage-point practical effect for a 0.10 bite change
are the same as the original registration. Their values are fixed in the new
specification and runner before the remaining outcomes are fetched. Failure
of a gate is INCONCLUSIVE; an estimable result below the direction threshold
is PARTIAL. Even a SUPPORTED direction can receive only descriptive
calibration credit: no causal, policy, school-score, or featured credit, and
no rescue of archived DiD records. The earlier Alabama peek must be disclosed
in every result packet.

Official references: [Census S2301 2024 table](https://data.census.gov/table/ACSST1Y2024.S2301), [Census table ZIP guidance](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/can-i-download-tables.html), [Census API key requirement](https://www.census.gov/data/developers/data-sets/acs-supplemental-data.html), and [2015 ACS one-year S2301 title change](https://www.census.gov/programs-surveys/acs/technical-documentation/table-and-geography-changes/2015/1-year.html).
