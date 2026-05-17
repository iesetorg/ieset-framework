# Resource Developmentalism Trade Data Acquisition - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Purpose: acquire or unblock a product-export concentration source for the hardened export-diversification outcome.

## Bottom Line

The fastest viable route is now the World Bank/WITS precomputed Herfindahl-Hirschman Product Concentration Index Export. It is not BACI or Comtrade product-line microdata, but it is a real product-concentration benchmark and is now loadable by the local runner as:

`wits:export_product_hhi_wits`

The deeper upgrade remains CEPII BACI HS6 or UN Comtrade product-line exports, because those would let us compute HHI, Theil, top-product shares, product counts, commodity shares, and manufacturing export shares from raw exporter-product-year lines.

## Acquired Local Files

World Bank/WITS metadata workbook:

- `data/manual/wits/herfindahl_hirschman_product_concentration_index_export_2026-02-09.xlsx`
- SHA-256: `f226108714a2a4985854178065edf328797a25a934d3f2ddee76e5fc0707452f`
- Source page: `https://datacatalog.worldbank.org/search/dataset/0064718/herfindahl-hirschman-product-concentration-index-export`

Raw annual bulk zips:

- Directory: `data/raw/wits/hhpci_export/`
- Files: `ed_hhpci_1988_export_csv.zip` through `ed_hhpci_2022_export_csv.zip`
- Count: 35 files

Loadable vintage:

- `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet`
- Rows: 4,669
- Reporter ISO3s: 207
- Years: 1988-2022
- Filter: `PartnerISO3 == WLD`
- Value: `Indicator`
- Supporting field retained: `number_of_products`

Manifest:

- `data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json`

The local generic runner can load the series via `wits:export_product_hhi_wits`.

## Source Notes

The World Bank Data Catalog page states that the HHI export index is a measure of the dispersion of trade value across an exporter's products; values close to 1 indicate concentration in very few products, while a decline over time can indicate diversification. The catalog lists the dataset as public under Creative Commons Attribution 4.0 and gives temporal coverage as 1988-2025.

The downloaded bulk workbook currently exposes HHPPCI annual zip paths for 1988-2022. It also contains later `ed_vre_2020_export_csv.zip` through `ed_vre_2022_export_csv.zip` paths, but those are not the HHPPCI index used here. Treat 1988-2022 as the verified local vintage coverage.

The annual CSV zips contain columns:

- `Classification`
- `Year`
- `ReporterISO3`
- `PartnerISO3`
- `Product`
- `NumberOfProducts`
- `Indicator`

The local vintage uses only exporter-to-world rows where `PartnerISO3 == WLD`.

## Route Ranking

| Route | Status | Use now | Why |
| --- | --- | --- | --- |
| World Bank/WITS HHPPCI export index | Acquired and loadable locally | Yes, as benchmark product-concentration outcome | Small public bulk files, no key, country-year HHI already computed, runner loads it. |
| CEPII BACI HS6 | Not downloaded locally | Next deep upgrade | Best microdata route: bilateral product-level trade, HS6, annual files, 200 countries, 5,000 products. Large files by HS revision. |
| UN Comtrade API | No local fetcher; key likely needed | Later robustness or microdata source | Official source and can provide HS/SITC product exports, but API and quota handling need implementation. |
| UNCTAD concentration/diversification index | Fetcher exists but not for this index | Fast official benchmark if WITS proves insufficient | Would require identifying and adding the relevant dataflow. Current local UNCTAD fetcher supports other aggregate series only. |
| WITS product-line exports | No local fetcher/product lines | Later | Could complement Comtrade, but current local result is precomputed HHI, not product-line data. |

## BACI / Comtrade Caveat

CEPII BACI remains the best source for a full product-line build. The current CEPII page describes BACI as bilateral trade flows for about 200 countries at the HS 6-digit product level, with annual CSV files and variables for year, product, exporter, importer, value, and quantity. The local repo currently has CEPII Gravity/BACI-derived aggregates only, not the BACI HS6 product archive.

Because the WITS HHI is already precomputed, it can support an export-product concentration benchmark but not the full derived outcome family:

- no local Theil from product shares yet
- no top-1/top-3/top-10 product shares yet
- no active product count thresholds beyond the provided `NumberOfProducts`
- no local commodity/manufacturing product-basket shares yet

## Integration Implications

Wave 2C is no longer fully blocked for a benchmark product-concentration outcome. It can now run a non-final prototype using:

- `wits:export_product_hhi_wits` as product concentration, where higher means more concentrated
- `derived:export_concentration_hhi_broad` as broad-sector robustness
- `derived:export_diversification_index` as broad-sector inverse-HHI robustness

Wave 2C is still blocked for a full product-line microdata design until BACI HS6 or Comtrade product lines are acquired.

## Exact Follow-Up Commands

To inspect the current WITS vintage:

```sh
python3 -c "import pandas as pd; p='data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet'; df=pd.read_parquet(p); print(df.shape); print(df.year.min(), df.year.max(), df.country_iso3.nunique())"
```

To verify runner loading:

```sh
python3 -c "import importlib.util; spec=importlib.util.spec_from_file_location('run_panel_fe','scripts/run_panel_fe.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); res=m.load_variable('wits:export_product_hhi_wits'); print(res[0].shape if res else None)"
```

To fetch BACI later, use the CEPII BACI download page and choose a single HS revision/version instead of mixing revisions. HS92 gives the longest current coverage, while HS17/HS22 are smaller and newer. Store the archive under `data/raw/baci/` or `data/manual/baci/`, then write a dedicated derived builder.

## Tracking Caveat

The generated raw/manual/vintage data files may be ignored by `.gitignore`. They exist locally, but ordinary `git status` shows only the JSON manifest and audit memo unless ignored data paths are force-added or ignore rules are revised.
