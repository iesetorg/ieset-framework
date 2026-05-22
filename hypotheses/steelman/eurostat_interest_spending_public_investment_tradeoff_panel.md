# Steelman - eurostat_interest_spending_public_investment_tradeoff_panel

Claim tested: Higher interest expenditure shares predict lower public investment or education/health spending in EU country-years outside monetary-sovereign conditions.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `public_debt_gdp` from `imf:GGXWDG_NGDP` and outcome
`investment_share` from `world_bank_wdi:NE.GDI.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
