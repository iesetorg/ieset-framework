# Steelman - capacity_water_sanitation_urbanization_health_dividend

Claim tested: Urban infrastructure investment lowers mortality and supports urban productivity only when municipal/state capacity is high; rapid urbanization without service delivery predicts worse health and weaker productivity.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `electricity_access` from `world_bank_wdi:EG.ELC.ACCS.ZS` and outcome
`under_five_mortality` from `world_bank_wdi:SH.DYN.MORT`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
