# Steelman - capacity_childcare_spending_female_lfp_housing_cost

Claim tested: Public childcare and family benefits raise female labour-force participation and fertility only when housing costs and childcare supply constraints are not binding; high transfers without supply expansion have weaker fertility/LFP effects.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `childcare_spending_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`female_labor_force_participation` from `world_bank_wdi:SL.TLF.CACT.FE.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
