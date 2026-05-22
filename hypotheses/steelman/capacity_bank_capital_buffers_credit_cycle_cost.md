# Steelman - capacity_bank_capital_buffers_credit_cycle_cost

Claim tested: Higher pre-crisis bank capital buffers reduce crisis output losses without permanently lowering credit growth in high-supervision states; in weak-supervision states, nominal capital ratios do not prevent credit busts.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `credit_gap` from `bis:WS_CREDIT_GAP` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
