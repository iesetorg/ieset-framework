# Steelman - child_family_benefits_female_lfp_fertility_panel

Claim tested: Childcare and family-benefit expansions raise female labor-force participation and fertility without lowering maternal employment; refuted if cash-only benefits reduce employment or fail to move fertility.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `family_benefit_expenditure_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`female_labor_force_participation` from `world_bank_wdi:SL.TLF.CACT.FE.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
