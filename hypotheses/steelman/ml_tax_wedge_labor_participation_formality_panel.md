# Steelman - ml_tax_wedge_labor_participation_formality_panel

Claim tested: higher labor tax wedges predict lower prime-age employment and higher informality over long windows, with larger effects in middle-income economies.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `tax_revenue_share` from `world_bank_wdi:GC.TAX.TOTL.GD.ZS` and outcome
`labor_force_participation` from `world_bank_wdi:SL.TLF.CACT.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
