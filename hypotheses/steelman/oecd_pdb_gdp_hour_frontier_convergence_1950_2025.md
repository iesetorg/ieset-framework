# OECD PDB GDP/hour frontier convergence

**Claim.** Countries farther below the annual OECD labour-productivity frontier subsequently grow faster in GDP per hour.

**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.

**Test.** `gdp_hour_growth ~ frontier_gap_lag + C(country) + C(year)`.
