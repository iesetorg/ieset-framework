# Steelman - ml_minimum_wage_bite_youth_informality_tradeoff

Claim tested: high minimum-wage bite raises wages for covered incumbents but predicts weaker youth employment and higher informal employment in low-productivity regions.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `minimum_wage_bite_proxy` from `oecd:MWUSD` and outcome
`unemployment_rate` from `world_bank_wdi:SL.UEM.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
