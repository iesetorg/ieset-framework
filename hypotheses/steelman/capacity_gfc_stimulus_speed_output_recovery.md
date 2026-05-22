# Steelman - capacity_gfc_stimulus_speed_output_recovery

Claim tested: During the 2008-2012 crisis, faster fiscal stimulus in high-capacity states predicted smaller employment losses and faster GDP recovery; in low-capacity/high-debt states, stimulus size had weaker recovery payoff and worse sovereign-risk outcomes.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `government_consumption_share` from `world_bank_wdi:NE.CON.GOVT.ZS` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
