# Capital deepening without TFP limit

**Claim.** Capital deepening alone is a weak predictor of labour-productivity growth once MFP contribution is included.

**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.

**Test.** `lp_growth ~ capital_deepening + tfp_contribution + C(country) + C(year)`.
