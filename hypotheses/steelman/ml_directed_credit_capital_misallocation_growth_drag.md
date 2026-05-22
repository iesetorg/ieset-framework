# Steelman - ml_directed_credit_capital_misallocation_growth_drag

Claim tested: directed-credit intensity predicts lower marginal product of capital and slower total factor productivity growth than market-priced credit allocation.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `private_credit_gdp` from `world_bank_wdi:FS.AST.PRVT.GD.ZS` and outcome
`tfp_index` from `pwt:rtfpna`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
