# Steelman - wits_food_tariffs_food_price_inflation_panel

Claim tested: Higher food import tariffs predict higher food-price inflation and worse poverty outcomes, especially in food-import-dependent countries.

This alias-batch version deliberately uses a local, loadable proxy:
treatment `applied_tariff_rate` from `wits:tariff_average` and outcome
`cpi_inflation` from `world_bank_wdi:FP.CPI.TOTL.ZG`.

The strongest skeptical reading is that the proxy may be too broad for
the original policy mechanism. A decisive first-pass coefficient should
therefore be treated as a queueing signal for bespoke replication, not
as a final scoreboard-ready verdict.
