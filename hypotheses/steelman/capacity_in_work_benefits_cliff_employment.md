# Steelman - capacity_in_work_benefits_cliff_employment

Claim tested: In-work benefits increase low-income employment when phaseout cliffs are smooth and administration is simple; sharp cliffs or complex means tests predict lower hours growth and weaker reemployment.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `family_benefit_expenditure_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`employment_rate` from `world_bank_wdi:SL.EMP.TOTL.SP.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
