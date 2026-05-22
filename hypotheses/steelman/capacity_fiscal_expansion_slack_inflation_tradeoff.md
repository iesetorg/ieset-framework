# Steelman - capacity_fiscal_expansion_slack_inflation_tradeoff

Claim tested: Discretionary fiscal expansion raises real output with limited inflation when unemployment is above its country-specific 10-year mean, but the output gain shrinks and inflation pass-through rises when unemployment is below that slack threshold.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `government_consumption_share` from `world_bank_wdi:NE.CON.GOVT.ZS` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
