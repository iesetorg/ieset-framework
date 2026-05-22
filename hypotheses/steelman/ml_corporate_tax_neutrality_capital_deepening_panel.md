# Steelman - ml_corporate_tax_neutrality_capital_deepening_panel

Claim tested: lower effective marginal tax rates on new investment predict faster capital deepening and manufacturing productivity growth than sector-specific investment credits.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `corporate_tax_rate` from `taxfoundation_itci:corporate_tax_rate_panel` and outcome
`investment_share` from `world_bank_wdi:NE.GDI.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
