# GDIM Backfill Attempt (2026-05-04)

## Objective

Unblock `intergenerational_mobility_cross_country` by sourcing a real
intergenerational-mobility outcome vintage.

## What Landed

- Downloaded the World Bank GDIM income mobility dataset to:
  `/tmp/gdim_income_mobility_2025.dta`
- Source URL used:
  `https://datacatalogfiles.worldbank.org/ddh-published/0066878/DR0095414/IGE_Munoz_VanderWeide_June2025.dta`
- File schema:
  - `code` (country code)
  - `IGE` (intergenerational earnings elasticity)
  - `source` (provenance string)

## Remaining Blocker

The current replication gate for
`intergenerational_mobility_cross_country` requires:

1. At least one mobility outcome series (partially solved by GDIM IGE), and
2. All three institutional channels, including two OECD channel series that
   still fail current fetch pathways.

Without those OECD channels, the hypothesis remains
`INCONCLUSIVE_DATA_PENDING`.

