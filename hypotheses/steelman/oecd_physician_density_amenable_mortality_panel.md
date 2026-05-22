# Steelman - oecd_physician_density_amenable_mortality_panel

Claim tested: Higher physician density predicts lower amenable mortality, with larger effects where public coverage or public health spending is higher.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `physician_density` from `world_bank_wdi:SH.MED.PHYS.ZS` and outcome
`amenable_mortality` from `oecd:HEALTH_STAT@DF_AMENABLE_MORT; world_bank_wdi:SH.DYN.MORT`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
