# IESET Mega Data Roundup 3

- generated_utc: `2026-05-05T212100Z`
- manifest: `data/manifests/fetch_run_2026-05-05T212100Z.yaml`
- jobs: 9
- ok: 4
- failed: 5
- rows landed: 21,749

## Landed

- `chinn_ito:kaopen_index_normalized` — 9,891 rows, 1970 to 2023 — Chinn-Ito capital account openness
- `chinn_ito:kaopen_raw` — 9,891 rows, 1970 to 2023 — Chinn-Ito raw KAOPEN factor
- `shiller:ie_data` — 1,833 rows, 1871 to 2023 — Shiller long-run equity, rates, and CAPE
- `shiller:home_price_index` — 134 rows, 1890 to 2023 — Shiller long-run US home-price index

## Failed / Needs Scrape Or Repair

- `chinn_ito:kaopen_components` — KeyError: "chinn_ito: component columns (k1..k4) not found; have ['cn', 'ccode', 'country_name', 'year', 'kaopen', 'ka_open']"
- `irr:era_classification_monthly` — IrrError: unknown IRR series_id 'era_classification_monthly'; one of ['era_classification_monthly_1940_2019', 'unified_market_analysis_1946_2021', 'anchor_currency_monthly_1946_2019']
- `irr:unified_market_analysis` — IrrError: unknown IRR series_id 'unified_market_analysis'; one of ['era_classification_monthly_1940_2019', 'unified_market_analysis_1946_2021', 'anchor_currency_monthly_1946_2019']
- `irr:anchor_currency_monthly` — IrrError: unknown IRR series_id 'anchor_currency_monthly'; one of ['era_classification_monthly_1940_2019', 'unified_market_analysis_1946_2021', 'anchor_currency_monthly_1946_2019']
- `hanke:hyperinflation_table` — TypeError: '<=' not supported between instances of 'float' and 'str'
