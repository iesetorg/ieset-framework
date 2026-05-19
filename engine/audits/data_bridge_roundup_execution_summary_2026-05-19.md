# Data-Bridge Roundup Execution Summary - 2026-05-19

## Purpose

Push the largest remaining data-bridge clusters for the hypothesis corpus:
OECD fiscal/output/labour/productivity aliases, BOJ/ECB monetary series,
WITS/Comtrade/UNCTAD trade series, WIPO innovation series, and IEA/IRENA
energy series.

## Runnability Movement

| Metric | Before | After | Movement |
| --- | ---: | ---: | ---: |
| READY specs | 1,511 | 1,530 | +19 |
| NEEDS_DATA specs | 101 | 82 | -19 |
| Total specs audited | 1,612 | 1,612 | 0 |

The current runnability snapshot is generated in
`engine/runnability.derived.yaml` and summarized in
`engine/runnability.report.md`.

## Data Landed

Six successful fetch manifests landed 2,463,106 rows.

| Cluster | Rows | Main sources landed |
| --- | ---: | --- |
| OECD productivity/labour bridge | 2,261,595 | `oecd:DSD_PDB`; `oecd:DSD_LFS_DF_LFS_INDIC` |
| WITS trade bridge | 103,574 | imports, exports, applied tariffs, tariff average, product concentration, HS6 product counts, product lines, high-tech exports |
| BOJ monetary bridge | 53,402 | M2 money stock, monetary base, policy/call-rate series |
| WIPO innovation bridge | 44,438 | total, resident, and non-resident patent applications; IP data-center mirror |
| ECB monetary bridge | 67 | deposit facility/policy-rate alias |
| IRENA energy bridge | 30 | solar PV and onshore wind LCOE |

## Manifests

- `data/manifests/fetch_run_2026-05-19T095056Z.yaml` - first full bridge sweep.
- `data/manifests/fetch_run_2026-05-19T095257Z.yaml` - repaired WITS import/tariff/product-concentration sweep.
- `data/manifests/fetch_run_2026-05-19T095746Z.yaml` - repaired BOJ money stock and monetary-base sweep.
- `data/manifests/fetch_run_2026-05-19T100506Z.yaml` - repaired BOJ policy-rate sweep.
- `data/manifests/fetch_run_2026-05-19T100517Z.yaml` - repaired WITS tariff/product-count sweep.
- `data/manifests/fetch_run_2026-05-19T100537Z.yaml` - repaired WITS export-value sweep.

## Fetcher Repairs

- Added `data.fetchers.wits` with WDI/WITS mirrors and WITS SDMX JSON support.
- Added `data.fetchers.wipo` using the World Bank WDI mirror for WIPO patent series.
- Added `data.fetchers.un_comtrade` with bounded official Comtrade API jobs.
- Rebuilt `data.fetchers.boj` around the official BOJ API with manual-drop fallback.
- Expanded `data.fetchers.ecb` shortcuts for deposit/policy-rate and yield aliases.
- Expanded `data.fetchers.iea` to probe public IEA product pages and preserve manual-drop fallback.
- Updated runnability aliases so newly landed canonical vintages count for common spec aliases.

## Still Blocked

- `un_comtrade` now has a fetcher, but the official API returned `401` without a subscription key.
- `iea` public pages did not expose usable official CSV/XLSX links for the targeted series through the robust/ZenRows probe; these still need manual-drop files or a different official API path.
- `unctad` bulk URLs returned `404`; the next pass should refresh UNCTAD dataflow IDs before another fetch attempt.
- Some OECD series remain exact-dataflow problems rather than missing-publisher problems, especially national accounts, ALMP, pensions, FDI, and tax shortcuts.
- FRED Japan mirrors remain optional because BOJ official vintages now cover the main Japan monetary bridge; FRED still requires `FRED_API_KEY`.
