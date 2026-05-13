# Post-2008 productivity hysteresis

**Claim.** OECD labour-productivity growth was persistently lower after 2008 than before 2008.

**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.

**Test.** `lp_growth ~ post_2008 + C(country)`.
