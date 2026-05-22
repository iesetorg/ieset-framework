# Steelman - capacity_energy_shock_transfers_vs_price_controls

Claim tested: Energy-shock relief works better as targeted transfers or temporary tax smoothing in high-capacity states; administered price controls/subsidies predict shortages, fiscal slippage, or lower investment where pass-through is suppressed for long periods.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `fossil_fuel_consumption_subsidies` from `owid:consumption-subsidies-for-fossil-fuels` and outcome
`cpi_inflation` from `world_bank_wdi:FP.CPI.TOTL.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
