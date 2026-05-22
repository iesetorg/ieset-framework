# Steelman - oecd_ict_sector_productivity_spillover_panel

Claim tested: Higher ICT-sector value-added or productivity growth predicts faster aggregate GDP-per-hour growth.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `internet_users` from `world_bank_wdi:IT.NET.USER.ZS` and outcome
`real_gdp_pc_growth` from `world_bank_wdi:NY.GDP.PCAP.KD.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
