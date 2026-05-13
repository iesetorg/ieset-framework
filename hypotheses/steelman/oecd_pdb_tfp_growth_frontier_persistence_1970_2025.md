# OECD PDB TFP growth persistence

**Claim.** OECD multifactor-productivity growth has country-level persistence after common year shocks.

**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.

**Test.** `tfp_growth ~ tfp_growth_lag + C(country) + C(year)`.
