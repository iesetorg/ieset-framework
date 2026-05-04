# Blocked Source Recovery Playbook

Generated: 2026-05-04

Purpose: convert the current blocked data bundles into reproducible vintages
without weakening the preregistered designs. Official publisher URLs remain the
canonical source; ZenRows/Scrapling are transport tools, not alternate evidence.

## Transport Rules

1. Prefer official machine APIs and stable bulk files.
2. If official public URLs return 403/Cloudflare/Akamai, use
   `data.fetchers._http.get`, which tries:
   - direct `requests`
   - `curl_cffi` Chrome impersonation
   - ZenRows when `ZENROWS_API_KEY` is set
3. Record `extra.http_transport` in the vintage manifest when a proxy transport
   is used.
4. Do not scrape paywalled/subscription data. For IEA paid products, use only
   free public data products or manual drops from an authorized user download.
5. Keep unit keys intact: country, state, county, technology, forecast vintage,
   or hourly/day-ahead timestamp. Collapsed national-year substitutes should
   remain inconclusive.

## Bundle 1: Intergenerational Mobility

Current landed:
- `owid:intergenerational-earnings-elasticity`

Still needed:
- `oecd:OECD.EDU.IMEP_DSD_EAG_FIN_DF_FIN_RESOURCES_1.0`
- `oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0`
- Optional robustness: `owid:share-of-children-in-the-bottom-quintile-who-make-it-to-the-top-quintile`

Solution:
- First try `scripts/fetch.py oecd ...` now that OECD uses the robust HTTP shim.
- If OECD still blocks or the URN resolver misses the new Data Explorer id, use
  Scrapling/ZenRows only to discover the exact CSV API URL from the Data
  Explorer page, then feed that URL/URN back into the OECD fetcher.
- Do not replace the education/housing channels with WDI GDP, Gini, or poverty.

Expected unlock:
- 17 linked claims after the bespoke partial-R2 and leave-one-out branch lands.

## Bundle 2: Minimum Wage

Current landed:
- `usdol:state_minimum_wage_history`

Still needed:
- `bls:LAU_state_teen_employment_population_ratio_panel`
- `bls:OEWS_state_p10_hourly_wage_panel`
- `bls:OES_state_median_hourly_wage_panel`
- `bls:QCEW_state_total_employment_panel`
- `bls:QCEW_county_NAICS722_employment_panel`
- `derived:minimum_wage_bite_ratio_subnational_panel`

Solution:
- Avoid the BLS API one-series path for large panels where public bulk flat
  files exist.
- QCEW: use BLS public CSV/ZIP annual files, preserving `area_fips`, `industry_code`,
  `own_code`, and year. County NAICS 722 should be built from annual county files.
- OEWS/OES: use BLS downloadable state XLS/ZIP files by year; extract p10 and
  median hourly wage fields. Use OES naming before the OEWS rename.
- Teen E/P: if LAU cannot supply age-specific state E/P, switch to CPS public
  microdata or BLS CPS state-age annual tables. Do not use national FRED teen E/P.
- Derived bite ratio: join `usdol` minimum wage to state p10/median hourly wages
  by state-year, then require coverage diagnostics before rerun.

Expected unlock:
- 27 linked claims across the minimum-wage cluster if state/county keys survive.

## Bundle 3: Nuclear Reliability And Prices

Still needed:
- `iea:industrial_electricity_price`
- `entsoe:day_ahead_price_volatility`
- LOLE/adequacy metrics
- fossil backup capacity factor

Solution:
- IEA: keep manual-drop as the default for official free Energy Prices
  workbooks; ZenRows can help discover the current public download URL, but the
  fetcher should still parse a stable CSV/XLSX vintage.
- ENTSO-E: add a first-class fetcher behind `ENTSOE_API_KEY`. This is better
  than scraping because ENTSO-E has a documented API and hourly timestamps.
- LOLE/adequacy: use ENTSO-E ERAA / national TSO public adequacy reports as
  manual-vintage tables if no API exists.
- Fossil backup capacity factor: derive from Ember/ENTSO-E generation by fuel
  divided by installed fossil capacity where coverage permits.

Expected unlock:
- 17 linked claims for the nuclear phaseout reliability/cost cluster.

## Bundle 4: China Renewables LCOE

Current landed:
- IRENA installed capacity via PxWeb.

Still needed:
- `irena:lcoe_solar_pv`
- `irena:lcoe_wind_onshore`

Solution:
- Use ZenRows/Scrapling to locate the official `Download data` workbook for
  IRENA Renewable Power Generation Costs.
- Store the workbook in `data/manual/irena/` if the URL is unstable.
- Existing `data.fetchers.irena` already parses manual LCOE drops by filename
  hint (`solar`, `wind`).

Expected unlock:
- 7 linked claims for the China renewables learning-curve hypotheses.

## Bundle 5: Wealth Tax Realized-vs-Forecast

Still needed:
- France ISF/IFI realized revenue and official forecasts.
- Norway 2022 wealth-tax hike realized revenue plus migration/outflow measures.
- Colombia 2022-2023 patrimonio tax forecast and realization.
- Spain grandes fortunas forecast and realization.

Solution:
- This should be a hand-curated public-finance panel, not a generic scraper.
- Create `data/manual/wealth_tax/revenue_forecast_realized.csv` with:
  `country_iso3,case_id,tax_name,forecast_vintage_year,revenue_year,
  forecast_revenue_local,realized_revenue_local,currency,source_url,
  methodology_url,notes`.
- Add a manual fetcher that writes this panel as a vintage and retains source
  URLs row-by-row.
- Use ZenRows/Scrapling only to retrieve public budget PDFs/HTML pages where
  treasury sites block direct requests.

Expected unlock:
- 17 linked claims once France is present and the multi-case chain is complete.

## Immediate Order

1. Probe OECD with the robust HTTP shim using `ZENROWS_API_KEY`.
2. Build BLS bulk panel fetchers for OEWS/OES and QCEW before rerunning any
   minimum-wage hypothesis.
3. Use manual-drop for IRENA LCOE and IEA Energy Prices unless ZenRows finds
   stable official file URLs.
4. Create the wealth-tax manual panel schema and fill France first.
5. Rerun only the affected hypotheses after unit-count and source-coverage
   diagnostics pass.
