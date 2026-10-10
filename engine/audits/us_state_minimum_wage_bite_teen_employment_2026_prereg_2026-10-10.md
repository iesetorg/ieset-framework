# Prospective source and design lock — 2026-10-10

This registration fixes one age-specific US state outcome before opening
selected ACS ratios or the pinned bite values. Its roster CSV has exactly
408 state-year keys (51 units × 2014–2018, 2021, 2023–2024), drawn using
the treatment vintage's state/year identifiers only. The frozen outcome
is Census ACS one-year Subject Table S2301 `S2301_C03_002E` (age 16–19
employment/population ratio); `S2301_C03_002M` is retained as uncertainty
metadata. Source URLs are `https://api.census.gov/data/{year}/acs/acs1/subject?get=NAME,S2301_C03_002E,S2301_C03_002M&for=state:*`.
The 2014 and 2024 Census API group pages identify the field, and the
2021 group exists. After this commit, fetch exact raw API responses, hash
them, lock a selected source slice, and only then fit the frozen model.

Earlier related public records are
`pcw100_us_mw_bite_ratio_employment_ratio` (all-age state ratio) and
`minimum_wage_median_youth_unemployment_2020_2024_v2` (national youth
unemployment). Archived high-bite DiD records remain archived.
