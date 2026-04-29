# BLOCKED — housing_cost_driven_real_wage_divergence

**Status:** Cannot run with currently-fetched vintages.

## Required data not available

The hypothesis is metro-level (not country-level) and requires:
- Metro-level median earnings: UK (ONS ASHE subnational), US (BLS QCEW metro), AUS (ABS Labour Force metro). None of these subnational fetchers are present in `data/vintages/`.
- Metro-level rents / housing prices: ONS/Land Registry metro rents, FHFA/Zillow metro indices, CoreLogic metro rents. Not fetched.
- Metro housing-supply elasticity coding sheet (Saiz 2010, Hilber-Vermeulen 2016, Kendall-Tulip 2018) — manual artifact under `data/manual/housing_supply_elasticity.csv` per spec; not present.
- Metro-level productivity (BEA metro GDP, ONS regional GVA, ABS state accounts) — not fetched.
- BIS WS_SPP residential property prices — present at vintages dir but only at country level; metro-level subseries not fetched.

The spec itself flags v2 promotion as data-gated on ONS / BEA / ABS native fetchers. v1 cannot be executed without metro panel construction.

## What would unblock

1. Native subnational fetchers for ONS, BEA, ABS.
2. Manual elasticity-coding artifact committed.
3. Metro-level rent + price aggregations.

## Action

No replication.py written. Re-attempt when the metro-level pipeline lands.
