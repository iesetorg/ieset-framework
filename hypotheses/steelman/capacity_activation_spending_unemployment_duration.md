# Steelman - capacity_activation_spending_unemployment_duration

Claim tested: Active labour-market spending reduces long-term unemployment only where case-management capacity and benefit conditionality are strong; passive benefit generosity without activation predicts longer unemployment duration.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `almp_spending_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`unemployment_rate` from `world_bank_wdi:SL.UEM.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
