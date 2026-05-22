# Steelman - ml_capital_market_depth_reallocation_productivity

Claim tested: deeper private capital markets predict faster reallocation of capital toward high-productivity firms and stronger aggregate TFP growth than bank-dominated systems with politically concentrated credit.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `private_credit_gdp` from `world_bank_wdi:FS.AST.PRVT.GD.ZS` and outcome
`tfp_index` from `pwt:rtfpna`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
