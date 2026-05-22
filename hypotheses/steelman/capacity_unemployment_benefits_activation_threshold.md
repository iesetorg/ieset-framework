# Steelman - capacity_unemployment_benefits_activation_threshold

Claim tested: More generous unemployment benefits do not lower employment when activation spending and case-management capacity are high; without activation, generosity predicts longer unemployment duration and lower employment rates.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `unemployment_benefit_expenditure_gdp` from `oecd:DSD_SOCX@DF_SOCX_AGG` and outcome
`employment_rate` from `world_bank_wdi:SL.EMP.TOTL.SP.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
