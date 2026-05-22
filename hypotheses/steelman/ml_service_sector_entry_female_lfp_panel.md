# Steelman - ml_service_sector_entry_female_lfp_panel

Claim tested: lower entry barriers in childcare, retail, transport, and personal services predict higher female labor-force participation through lower household-service prices and more flexible jobs.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `service_entry_barriers` from `oecd_pmr:BARRIER_ENTRY` and outcome
`female_labor_force_participation` from `world_bank_wdi:SL.TLF.CACT.FE.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
