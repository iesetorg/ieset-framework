# Steelman - capacity_public_investment_execution_private_capital_complement

Claim tested: Public investment complements private investment and productivity only in high-execution states; in low government-effectiveness states, higher public capital formation predicts weaker private investment shares and no TFP improvement.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `gross_fixed_capital_formation` from `world_bank_wdi:NE.GDI.FTOT.ZS` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
