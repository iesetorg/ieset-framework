# Steelman - ml_customs_simplification_trade_cost_growth

Claim tested: customs simplification and shorter border delays predict lower trade costs and faster small-exporter growth than tariff cuts alone.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `applied_tariff_rate` from `wits:weighted_mean_applied_tariff` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
