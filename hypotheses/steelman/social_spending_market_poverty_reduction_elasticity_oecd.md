# Steelman - social_spending_market_poverty_reduction_elasticity_oecd

Claim tested: Higher social spending reduces market-income poverty more strongly where benefits are more cash-and-service universal, and the claim is weakened if poverty falls only through accounting transfers with no improvement in employment or material deprivation.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `welfare_state_size` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`poverty_headcount` from `world_bank_wdi:SI.POV.DDAY`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
