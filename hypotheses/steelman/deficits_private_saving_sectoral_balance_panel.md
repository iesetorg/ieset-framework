# Steelman - deficits_private_saving_sectoral_balance_panel

Claim tested: Government deficits are associated with higher private-sector net saving, especially when current-account balances are stable; the claim is refuted if private saving does not co-move after accounting identities and valuation changes are handled.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `fiscal_balance_proxy` from `world_bank_wdi:GC.NLD.TOTL.GD.ZS` and outcome
`current_account_balance` from `world_bank_wdi:BN.CAB.XOKA.GD.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
