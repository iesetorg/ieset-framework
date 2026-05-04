# Wealth Tax Manual Panel

Use this directory for the multi-country realized-vs-forecast panel required by
`wealth_tax_capital_flight_revenue_yield_gap`.

Copy `revenue_forecast_realized.template.csv` to
`revenue_forecast_realized.csv`, then fill one row per country/tax/revenue-year
forecast vintage. Keep official source URLs row-by-row.

Minimum coverage target:

- France ISF/IFI realized revenue and official forecasts.
- Norway 2022 wealth-tax hike realized revenue and migration/outflow measures
  if present in source notes.
- Colombia 2022-2023 patrimonio tax forecast and realization.
- Spain grandes fortunas forecast and realization.

Run:

```bash
venv/bin/python scripts/fetch.py wealth_tax_manual revenue_forecast_realized
```
