# Steelman - ml_energy_price_controls_shortage_fiscal_burden

Claim tested: sustained household fuel or electricity price controls predict higher shortage frequency, larger fiscal subsidy burdens, and lower energy-sector investment.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `fossil_fuel_consumption_subsidies` from `owid:consumption-subsidies-for-fossil-fuels` and outcome
`electricity_access` from `world_bank_wdi:EG.ELC.ACCS.ZS`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
