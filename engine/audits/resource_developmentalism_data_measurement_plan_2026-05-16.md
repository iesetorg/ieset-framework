# Resource Developmentalism Data Measurement Plan - 2026-05-16

Worker: B, data measurement lane

Write scope: `engine/audits/resource_developmentalism_data_measurement_plan_2026-05-16.md`

## Bottom Line

The current `derived:export_diversification_index` should be treated as `broad_wdi_proxy`, not as a dispositive export-product diversification measure. It is a reproducible, useful screen, but it is built from only four broad WDI merchandise-export share buckets plus a residual: agricultural raw materials, fuels, manufactures, ores/metals, and other. That is too coarse for the preregistered claim about long-run export diversification.

The highest-value measurement upgrade is an exporter-product-year concentration vintage. No local BACI HS6, UN Comtrade product-level, or WITS product-level archive is currently visible. Local CEPII Gravity/BACI-derived vintages exist, but they are collapsed to country-year/dyad aggregates and cannot produce product HHI, Theil, top-product shares, or product counts without the underlying product lines.

## Local Inventory

| Measurement area | Local status | Evidence from local files | Use now |
| --- | --- | --- | --- |
| Broad export diversification proxy | Present | `data/vintages/derived/export_diversification_index@2026-05-16T085311Z.parquet`, 9,623 rows, 241 countries, 1962-2024 | Keep as fallback/robustness; label `broad_wdi_proxy` |
| Broad export concentration HHI | Present | `data/vintages/derived/export_concentration_hhi_broad@2026-05-16T085311Z.parquet`, same coverage | Use as sign-check mirror of diversification |
| WDI broad export shares | Present | `TX.VAL.AGRI.ZS.UN`, `TX.VAL.FUEL.ZS.UN`, `TX.VAL.MANF.ZS.UN`, `TX.VAL.MMTL.ZS.UN` | Inputs to broad proxy only |
| UNCTAD | Fetcher exists, no local vintage found | `data/fetchers/unctad.py` supports FDI, total merchandise trade, services, and GVC; no `data/vintages/unctad` directory found | Not currently usable for concentration without fetcher/dataflow extension |
| UN Comtrade | Publisher registered, fetcher pending, no local vintage | `data/fetchers/publishers.yaml` marks `un_comtrade` pending and key-required | Future primary/robustness source |
| WITS | No fetcher or local vintage found | Prior inventories flag WITS absent/API-registration needed | Future tariff/trade-policy controls, not current outcome source |
| CEPII Gravity/BACI aggregates | Present | `data/vintages/cepii/gravity_exposure_panel@2026-05-15T175027Z.parquet`, 16,366 rows, 243 countries, 1948-2021; BACI tradeflow aggregates 1996-2020 | Useful controls/secondary outcomes, not product concentration |
| BACI product-level | Not visible locally | `data/raw/cepii/Gravity_csv_V202211.zip` exists; no BACI HS6 product archive found | Needed for primary upgrade |
| PWT TFP | Present | `data/vintages/pwt/rtfpna@2026-05-05T195242Z.parquet`, 6,407 non-null values, 183 countries, 1950-2019 | Outcome family input; compute log/percent growth windows explicitly |
| Manufacturing VA share | Present | `data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet`, 9,797 non-null values, 262 countries, 1960-2025 | Secondary outcome |
| WDI resource rents | Present | Total rents, oil rents, gas rents, mineral rents present | Core controls and resource-type split |
| WDI coal/forest rents | Not visible locally | No `NY.GDP.COAL.RT.ZS` or `NY.GDP.FRST.RT.ZS` vintage found | Fetch later if source supports |
| IMF PCPS commodity prices | Present for selected series | Brent oil, gas Europe, copper, metals index, wheat, maize, all commodities vintages present | Build commodity price-shock controls after exporter mix is measured |

## Current Proxy Classification

`derived:export_diversification_index` should be renamed in analysis notes to:

`export_diversification_broad_wdi_proxy = 1 - HHI([ag raw materials, fuels, manufactures, ores/metals, residual other])`

Important limitations:

- It has at most five buckets, so it cannot distinguish a country exporting one manufactured product from one exporting a wide set of manufactured products.
- The residual bucket is mechanically large for countries with services exports, nonclassified merchandise, or WDI category gaps.
- It captures broad sector movement, not product variety, product concentration, or commodity dependence at HS/SITC line level.
- It is still valuable for long historical coverage and as a transparent fallback if product-level coverage collapses.

## Source-Quality Ladder

| Tier | Source | Quality judgment | Role in hardened design |
| --- | --- | --- | --- |
| 1 | CEPII BACI HS6 exporter-product-year archive, if authorized and locally installed | Best primary option for 1996 onward: harmonized bilateral trade, product detail, exporter-year aggregation possible | Primary product concentration for 1996-2020/2022-style windows; best for HHI, Theil, top shares, product counts |
| 2 | UN Comtrade HS/SITC product-level exports | Strong official source with longer history, but classification changes and API limits require careful harmonization | Primary or pre-1996 extension; robustness against BACI |
| 3 | UNCTAD concentration/diversification/product indices | Official and convenient if the relevant dataflow can be added, but index construction may be less transparent than product microdata | Fast primary if fetched successfully; benchmark against product-built measures |
| 4 | CEPII Gravity BACI aggregate country-year measures | High-quality but already collapsed; useful for total tradeflow and manufacturing trade share, not product concentration | Controls/secondary outcomes only |
| 5 | WDI broad merchandise export shares | Very broad, high-coverage, reproducible | Fallback screen and robustness label only |

## Derived Vintage Design

When implementation is authorized, build a new derived manifest with country-year vintages:

1. `export_product_hhi`
   - For exporter `c`, year `t`, product `p`: `s_cpt = export_value_cpt / sum_p export_value_cpt`.
   - `HHI_ct = sum_p s_cpt^2`.
   - Higher means more concentrated.

2. `export_product_diversification_hhi_inverse`
   - `1 - HHI_ct`, optionally also normalized by product count as `(1 - HHI) / (1 - 1/N_ct)`.
   - Higher means more diversified.

3. `export_product_theil_concentration`
   - Use exporter-year product shares against equal product-share benchmark.
   - Keep zero-product treatment explicit; do not impute missing exporter-years as zero trade.

4. `export_top1_share`, `export_top3_share`, `export_top10_share`
   - Sum largest product shares within exporter-year.
   - These are intuitive and robust to noisy small lines.

5. `export_product_count_active`
   - Count products with positive exports and a minimum materiality threshold.
   - Recommended thresholds: any positive, at least USD 10,000, and at least 0.01 percent of exporter-year exports.

6. `commodity_export_share_product`
   - Map product codes to fuels, mining/metals, agriculture/raw materials, and other commodities.
   - This should sit beside WDI rents, not replace them.

7. `manufacturing_export_share_product`
   - From product classification, to complement WDI `TX.VAL.MANF.ZS.UN` and CEPII `gravity_manuf_tradeflow_baci_share`.

## Resource-Rent and Price Controls

Use WDI rent measures as annual resource-dependence controls:

- `NY.GDP.TOTL.RT.ZS`: total natural resource rents, available locally.
- `NY.GDP.PETR.RT.ZS`: oil rents, available locally.
- `NY.GDP.NGAS.RT.ZS`: natural gas rents, available locally.
- `NY.GDP.MINR.RT.ZS`: mineral rents, available locally.
- Add coal and forest rents only after fetching/confirming local vintages.

Commodity price shocks should be derived from local IMF PCPS series only after an exporter-mix baseline is available. Recommended construction:

- Annualize monthly PCPS series by calendar-year average.
- Compute real log price changes or deviations from 5-year moving averages.
- Weight each price shock by lagged commodity export share or lagged WDI rent subtype.
- Keep unweighted global price controls as robustness only; they do not capture country exposure.

Locally visible PCPS candidates include Brent oil (`POILBRE`), gas Europe (`PNGASEU`), copper (`PCOPP`), metals index (`PMETA`), wheat (`PWHEAMT`), maize (`PMAIZMT`), and all commodities (`PALLFNF`).

## Coverage Gates

Before replacing the broad WDI proxy, require:

- Product-level exporter-year totals reconcile to known total goods exports within a documented tolerance.
- Country-year coverage for the hypothesis sample is not worse than the WDI proxy without a clear, preregistered reason.
- Treated country coverage is reported separately from total country coverage.
- Product classification version is recorded in the manifest.
- Missing product-level exporter-years are missing, not zero.
- Commodity-export and manufacturing-export mappings are versioned and auditable.

## Recommended Hardened Measurement Order

1. Keep the current run as research-only and relabel the current outcome as `broad_wdi_proxy`.
2. Add an exporter-product-year primary source before any scoreboard-safe claim: CEPII BACI HS6 if available locally/download-authorized; otherwise UN Comtrade; otherwise UNCTAD concentration/diversification as a fast official benchmark.
3. Build the full concentration family: HHI, inverse HHI, Theil, top-1/top-3/top-10 shares, active product count, commodity export share, manufacturing export share.
4. Preserve WDI broad proxy as a long-run robustness outcome because it covers 1962-2024.
5. Use PWT `rtfpna` and WDI manufacturing VA share as separate outcomes, not silent loaded variables.
6. Add rent-subtype controls and commodity price shocks only with explicit exposure weights.

## Stop/Blockers

- Do not claim product diversification from the current WDI broad proxy.
- Do not use CEPII Gravity BACI aggregates as product concentration; they are already collapsed.
- Do not score the hypothesis until the primary export-concentration measure and TFP growth window are both explicitly estimated.
- If no product-level source is authorized, classify the result as research-only and report the current estimate as a broad-sector screening result.
