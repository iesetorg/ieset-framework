# Steelman - food_production_trade_openness_resilience_panel

Claim tested: Countries with both higher domestic food-production growth and higher food-trade openness have smaller food-price and poverty spikes after global commodity-price shocks.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `agriculture_value_added_share` from `world_bank_wdi:NV.AGR.TOTL.ZS` and outcome
`poverty_headcount` from `world_bank_wdi:SI.POV.DDAY`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
