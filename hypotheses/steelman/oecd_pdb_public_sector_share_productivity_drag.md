# Public-sector share productivity drag

**Claim.** A larger public-administration, education, and health GVA share predicts slower subsequent total-economy labour-productivity growth.

**Data.** Latest landed OECD Productivity Database vintage, with PMR added only for the market-reform specification.

**Test.** `lp_growth ~ public_gva_share_lag + C(country) + C(year)`.
