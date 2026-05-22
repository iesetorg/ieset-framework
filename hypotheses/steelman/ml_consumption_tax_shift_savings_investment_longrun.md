# Steelman - ml_consumption_tax_shift_savings_investment_longrun

Claim tested: revenue-neutral tax shifts from income taxation toward broad consumption taxation predict higher household saving and private investment, without systematically weaker lower-decile consumption growth when transfers are controlled.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `tax_revenue_share` from `world_bank_wdi:GC.TAX.TOTL.GD.ZS` and outcome
`investment_share` from `world_bank_wdi:NE.GDI.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
