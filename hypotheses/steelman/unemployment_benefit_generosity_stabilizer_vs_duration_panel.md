# Steelman - unemployment_benefit_generosity_stabilizer_vs_duration_panel

Claim tested: More generous unemployment benefits reduce household-income losses and recession depth, but the strongest claim is refuted if they materially lengthen unemployment duration after controlling for labor-demand shocks and activation spending.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `unemployment_benefit_expenditure_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`unemployment_rate` from `world_bank_wdi:SL.UEM.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
