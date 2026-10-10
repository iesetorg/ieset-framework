# ACS teen-employment source access — 2026-10-10

The prospective registration was committed as `ab65c5a2565152ec5843c56c12fc64e15ec2672b`.
The key-only check passed: 408 fixed US state-year keys, 51 states, eight exact
years, and a byte-matched local wage-bite vintage. No selected outcome or
treatment magnitude was read before that registration.

An official-source search found no keyless Census bulk file for the exact
S2301 estimate/MOE pair: the ACS Summary File distributes B/C detailed
tables, not Subject Table S2301. The 2014 S2301 metadata labels C03
"Employed" where later metadata says "Employment/Population Ratio"; its
measurement equivalence must be checked before this frozen multi-year
contrast can receive any result. A B23001-derived replacement would be a
different measurement and is outside this registration.

The first official Census API fetch returned HTTP 200 with an HTML **Missing
Key** page rather than JSON. Census now states that all data queries require
an API key, including the ACS one-year Subject Table endpoint. There is no
`CENSUS_API_KEY` in the current environment. The data.census.gov table page
also failed to load in the browser with a server 500 response. No outcome
values were ingested or source lock produced.

`scripts/fetch_acs_teen_with_key_2026.py` is an access-only adapter added
after registration, before any successful selected-data request. It passes a
key from the environment for the **same** publisher endpoint, years,
geography, and fields frozen in the registered runner. It does not save or
print the key. Once a key is available, run the adapter, inspect the raw
responses and selected slice, commit the source lock separately, then run the
frozen estimator and replay it. Until then, this hypothesis stays archived
and contributes zero public conversion credit. Do not substitute another
dataset or loosen the frozen rule to fill the gap.

Official references: [Census ACS Subject Tables and Summary File](https://www.census.gov/programs-surveys/acs/data/data-tables.html); [current API key requirement](https://api.census.gov/data/2024/acs/acs1/subject/examples.html); [2014 S2301 metadata](https://api.census.gov/data/2014/acs/acs1/subject/groups/S2301.html); [2024 S2301 metadata](https://api.census.gov/data/2024/acs/acs1/subject/groups/S2301.html).
