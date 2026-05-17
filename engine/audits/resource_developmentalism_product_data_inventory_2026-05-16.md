# Resource Developmentalism Product Data Inventory - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Worker: Wave 2B, product-level export measurement local inventory

Write scope: `engine/audits/resource_developmentalism_product_data_inventory_2026-05-16.md`

## Bottom Line

No directly usable exporter-product-year export data is present locally. I found WDI broad export-share vintages and CEPII Gravity/BACI-derived aggregate tradeflow vintages, but these are collapsed to country-year or dyad-year aggregates and cannot produce product-level HHI, Theil, top-product shares, or active product counts.

Wave 2C is blocked on product-level data acquisition for the export diversification outcome. A fallback prototype can still use the existing broad WDI proxy, but it must remain labeled `broad_wdi_proxy` and should not be treated as product diversification evidence.

## Search Scope

Local search covered:

- `data/vintages/`
- `data/raw/`
- `data/manual/`
- `data/fetchers/`
- `data/manifests/`
- the existing Wave 2 input audits:
  - `engine/audits/resource_developmentalism_swarm_synthesis_2026-05-16.md`
  - `engine/audits/resource_developmentalism_data_measurement_plan_2026-05-16.md`

Product-source keywords checked included `BACI`, `Comtrade`, `WITS`, `UNCTAD`, `HS6`, `SITC`, `product`, `trade`, `export`, `concentration`, and `diversification`.

## Product-Level Source Inventory

| Source | Local paths / evidence | Coverage and file type | Status | Product-HHI usability |
| --- | --- | --- | --- | --- |
| CEPII BACI HS6 product archive | No `data/vintages/baci`, `data/raw/baci`, `data/manual/baci`, or HS6 BACI archive found. CEPII local files are Gravity, not the BACI HS6 product archive. | Absent locally. | Absent / acquisition-needed. | Not usable. Need BACI product lines before HHI/Theil/top shares/product count can be built. |
| UN Comtrade product exports | `data/fetchers/publishers.yaml` registers `un_comtrade` with endpoint `https://comtradeapi.un.org/data/v1/get`, `auth_required: true`, `auth_env_var: UN_COMTRADE_KEY`, `status: pending`; no `data/fetchers/un_comtrade.py`; no `data/vintages/un_comtrade`, `data/raw/un_comtrade`, or `data/manual/un_comtrade`. | Absent locally; publisher metadata only. | Key-needed and fetcher-needed. | Not usable until the API key, fetcher, and HS/SITC export pulls exist. |
| WITS product-level trade | No WITS/world_bank_wits fetcher or publisher entry found in `data/fetchers/` or `data/fetchers/publishers.yaml`; no `data/vintages/wits`, `data/raw/wits`, or `data/manual/wits`. `data/manifests/coverage.derived.yaml` contains unresolved WITS raw tokens, but not data. | Absent locally. | Absent / fetcher-needed / possibly registration-needed. | Not usable. |
| UNCTAD concentration/diversification/product indices | `data/fetchers/unctad.py` exists and `data/fetchers/publishers.yaml` marks `unctad` ready. Supported fetcher series are `US.FDI`, `US.FDIstock`, `US.TradeMerchTotal`, `US.TradeServ`, and `US.GVCParticipation`. No `data/vintages/unctad`, `data/raw/unctad`, or `data/manual/unctad`. | Fetcher exists, but no local vintage. Supported trade series are aggregate matrix/services/GVC, not product-level concentration indices. | Fetcher extension-needed or fetch-needed for the relevant index dataflow. | Not currently usable for product HHI. A fetched UNCTAD concentration index could be a benchmark, but not a transparent product-line build unless the underlying product lines are fetched. |
| Other product-level trade archive | Filename and directory searches did not find local HS6/SITC/product trade archives under `data/vintages`, `data/raw`, or `data/manual`. | Absent locally. | Absent. | Not usable. |

## Aggregate Trade Data Found

These files are useful, but they are not product-level sources.

| Local source | Exact paths | Coverage / shape | File type | Usability |
| --- | --- | --- | --- | --- |
| CEPII Gravity raw zip | `data/raw/cepii/Gravity_csv_V202211.zip` | Zip contains `Gravity_V202211.csv` plus 11 country/label CSVs. Main gravity CSV has dyad-year records, not product records. | Zip of CSV files. | Useful for dyad/country-year aggregate trade controls. Not usable for product HHI. |
| CEPII Gravity dyad parquet | `data/vintages/cepii/cepii_gravity_V202211@2026-05-02T212753Z.parquet` | 4,699,296 rows, 87 columns, 1948-2021, 243 origin ISO3s and 243 destination ISO3s. Relevant trade columns are `tradeflow_baci` and `manuf_tradeflow_baci`; there is no HS/product code column. | Parquet. | Dyad-year aggregate only. Can support bilateral tradeflow/manufacturing-share controls, not exporter-product concentration. |
| CEPII Gravity exposure panel | `data/vintages/cepii/gravity_exposure_panel@2026-05-15T175027Z.parquet`; manifest `data/manifests/fetch_run_2026-05-15T175027Z.yaml` | 16,366 rows, 243 countries, 1948-2021. Manifest says directed dyads were collapsed by origin country-year. BACI tradeflow fields are present only as aggregate country-year fields. | Parquet plus manifest YAML. | Collapsed country-year panel. Not usable for product HHI/Theil/top-product shares/product counts. |
| CEPII BACI aggregate series | `data/vintages/cepii/gravity_total_tradeflow_baci@2026-05-15T175027Z.parquet`; `data/vintages/cepii/gravity_manuf_tradeflow_baci_share@2026-05-15T175027Z.parquet`; `data/vintages/cepii/gravity_fta_tradeflow_baci_share@2026-05-15T175027Z.parquet`; `data/vintages/cepii/gravity_fta_manuf_tradeflow_baci_share@2026-05-15T175027Z.parquet` | Each has 5,518 rows, 227 countries, 1996-2020. Manifest defines `gravity_total_tradeflow_baci` as the sum of observed CEPII BACI tradeflow over active foreign partners and `gravity_manuf_tradeflow_baci_share` as manufacturing tradeflow share of observed BACI tradeflow. | Parquet plus manifest YAML. | Directly usable for aggregate tradeflow and manufacturing-trade-share robustness only. Not product concentration. |
| WDI broad export share inputs | `data/vintages/world_bank_wdi/TX.VAL.AGRI.ZS.UN@2026-05-12T132702Z.parquet`; `data/vintages/world_bank_wdi/TX.VAL.FUEL.ZS.UN@2026-04-30T115204Z.parquet`; `data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet`; `data/vintages/world_bank_wdi/TX.VAL.MMTL.ZS.UN@2026-04-30T131203Z.parquet` | Annual WDI panels. Non-null rows: agricultural raw materials 8,539; fuels 9,471; manufactures 9,903; ores/metals 9,786. Years span 1960-2025 in the files. | Parquet. | Inputs to broad-sector proxy only. SITC section/group definitions are too coarse for product HHI. |
| Derived broad export proxy | `data/vintages/derived/export_diversification_index@2026-05-16T085311Z.parquet`; `data/vintages/derived/export_concentration_hhi_broad@2026-05-16T085311Z.parquet`; `data/vintages/derived/export_share_other_residual@2026-05-16T085311Z.parquet`; manifest `data/manifests/fetch_run_export_diversification_2026-05-16T085311Z.yaml`; builder `scripts/build_export_diversification_vintage.py` | 9,623 rows, 241 countries, 1962-2024. Recipe uses WDI shares for agricultural raw materials, fuels, manufactures, ores/metals, plus residual other. | Parquet plus manifest YAML and local builder script. | Directly usable as `broad_wdi_proxy` only. It is a 4-bucket plus residual HHI/diversification measure, not product-level concentration. |

## Measurement Implications

The local aggregate sources cannot be promoted into product-level measures:

- Country-year WDI broad shares can only form a broad-sector HHI.
- CEPII Gravity/BACI fields are already summed over partner flows and have no product dimension.
- Dyad-level tradeflow variation is not product variety. It could support partner concentration or market-access controls, but not product HHI, product Theil, top-product shares, or active product counts.
- Manufacturing export share from CEPII or WDI is useful as a secondary manufacturing-exposure measure, not as a substitute for product-level manufacturing classification.

## Conditional Product Vintage Recipe

Do not build a product vintage until a source with exporter, year, product code, export value, and classification metadata exists locally. Once BACI HS6, UN Comtrade HS/SITC, WITS product exports, or equivalent product lines are acquired, the derived vintage should:

1. Keep export flows only, record product classification/revision, and preserve missing exporter-years as missing rather than zero.
2. Aggregate to exporter-product-year: `export_value_cpt = sum_partner export_value_cpdt`.
3. Compute exporter-year total exports and product shares: `s_cpt = export_value_cpt / sum_p export_value_cpt`.
4. Emit `export_product_hhi = sum_p s_cpt^2`.
5. Emit inverse/normalized diversification, including `1 - HHI` and optionally `(1 - HHI) / (1 - 1 / N_ct)` where `N_ct` is active product count.
6. Emit Theil concentration, preferably `sum_p s_cpt * log(s_cpt / (1 / N_ct))`, with a documented normalization choice.
7. Emit `export_top1_share`, `export_top3_share`, and `export_top10_share` from sorted product shares.
8. Emit active product counts under multiple materiality thresholds: positive value, at least USD 10,000, and at least 0.01 percent of exporter-year exports.
9. Map product codes to commodity baskets for `commodity_export_share_product`.
10. Map product codes to manufacturing baskets for `manufacturing_export_share_product`.
11. Write a derived manifest pinning source paths, hashes, classification revision, country-code mapping, units/currency, missingness rules, and reconciliation to total goods exports.

## Acquisition Checklist

Preferred route:

1. Acquire CEPII BACI HS6 annual product-level files locally, with official country/product code dictionaries.
2. If BACI cannot be installed, implement `data/fetchers/un_comtrade.py`, set `UN_COMTRADE_KEY`, and fetch annual HS/SITC export product lines by reporter/year.
3. If Comtrade is quota-blocked, extend `data/fetchers/unctad.py` to fetch the relevant concentration/diversification/product-index dataflow as a fast benchmark, while keeping it separate from a product-line build.
4. If WITS is chosen, add a real publisher/fetcher entry before treating any `world_bank_wits` raw tokens in `coverage.derived.yaml` as usable data.
5. After acquisition, report coverage for treated subtype and comparator subtype once the Wave 2A subtype panel is available.

## Wave 2C Gate

Wave 2C should remain blocked for the product-level export concentration outcome. It can only proceed as a hardened prototype after product lines or official product/concentration indices are fetched and manifested. Without that acquisition, Wave 2C can run only a broad-sector robustness prototype using `derived:export_diversification_index` and `derived:export_concentration_hhi_broad`, clearly labeled as non-product WDI proxies.
