# Steelman - automatic_stabilizers_recession_depth_recovery_panel

Claim tested: Larger automatic stabilizers reduce peak-to-trough GDP losses and poverty spikes during recessions, but may trade off against recovery speed if labor-market reentry is weak.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `welfare_state_size` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`unemployment_rate` from `world_bank_wdi:SL.UEM.TOTL.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
