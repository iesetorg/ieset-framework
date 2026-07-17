# Graduation Data Pack F2 - Macro / Trade / Labour Source Pack - 2026-05-16

Scope: FRED, IMF, BOJ, BLS, ECB, ILOSTAT, Eurostat, WITS / Comtrade / UNCTAD.

Rules followed: planning and audit only. No data fetched. No files edited except this memo.

## Inputs Read

- `internal research notes`
- `engine/audits/broad_hypothesis_graduation_plan_2026-05-16.md`
- `engine/audits/resource_developmentalism_trade_data_acquisition_2026-05-16.md`
- `engine/audits/wits_comtrade_data_spine_plan_2026-05-12.md`
- `data/fetchers/publishers.yaml`
- Fetchers: `fred.py`, `imf_weo.py`, `imf_ifs.py`, `imf_pcps.py`, `boj.py`, `bls.py`, `ecb.py`, `ilostat.py`, `eurostat.py`, `unctad.py`
- Manifests/vintages visible for the lane, especially `data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json`

Read-only scans used:

```sh
python3 scripts/audit_inconclusive_load.py
python3 scripts/run_inconclusive_campaign.py --publishers fred,imf,imf_pcps,boj,bls,ecb,ilostat,eurostat,wits,un_comtrade,unctad --top 160 --per-publisher 0 --include-blocked
```

## Bottom Line

The highest-yield F2 action is not one giant fetch. It is a three-part batch:

1. Clear stale/alias blockers where data already exist (`ilostat:unemployment_rate`, `imf_pcps:POILBRE`, several FRED/BLS base series).
2. Run a small authenticated FRED plus targeted BLS/ECB/Eurostat/ILOSTAT fetch set.
3. Treat WITS/Comtrade/UNCTAD as a split lane: WITS HHI is now a real benchmark outcome, but tariff/product-line Comtrade remains fetcher/key blocked.

Broad source-readiness pressure from the graduation plan:

| Family | unresolved token references | Local feasibility now |
| --- | ---: | --- |
| IMF | 74 | Mixed: WEO/PCPS ready; IFS/BOP/AREAER manual-drop; many aliases stale. |
| FRED | 49 | Ready fetcher, but `FRED_API_KEY` required. Many current blockers already materialized and only need rerun/alias cleanup. |
| BOJ | 39 | Fetcher is manual-drop despite publisher endpoint being web; use `data/manual/boj/`. |
| BLS | 37 | Fetcher ready for standard series plus LAU/QCEW/OEWS panels; key optional but strongly recommended for fanouts. Several cited series are not valid BLS IDs. |
| ECB | 35 | Fetcher ready; many current blockers are shortcut/storage alias issues. |
| ILOSTAT | 28 | Fetcher ready; real indicator codes work, informal names need aliasing. |
| Eurostat | 21 | Fetcher ready for real dataset codes; shorthand names need lookup. |
| UN Comtrade | 11 | Publisher metadata only: pending, key-required, no fetcher. |
| WITS | 9 | HHI benchmark now loadable as `wits:export_product_hhi_wits`; tariffs/product lines still fetcher-needed. |
| UNCTAD | 8 | Fetcher exists but previous bulk URLs failed; current source tokens are mostly unsupported aliases. |

Current inconclusive diagnostics have 67 unresolved unique F2 publisher/series pairs after excluding materialized vintages. The dry-run batch classified blockers as:

| Blocker | unique series |
| --- | ---: |
| missing `FRED_API_KEY` | 19 |
| missing `BLS_API_KEY` under campaign logic | 13 |
| no ready fetcher registered | 6 |
| nominally fetchable by current registry | 29 |

Note: `BLS_API_KEY` is optional in `data/fetchers/bls.py`, but the campaign planner treats any publisher with an auth env var as blocked. For single BLS series, no-key fetches can work within low public limits; for LAU fanouts, use the key.

## Ranked Current Missing Series

Counts below are current inconclusive missing-token mentions, not guaranteed graduations. Feasibility is the practical chance the next worker can clear the missing-token blocker without new source research.

| Rank | Series/token | Current unlock count | Feasibility | Required action |
| ---: | --- | ---: | --- | --- |
| 1 | `ilostat:unemployment_rate` | 3 | High | Already bridged to `ilostat:UNE_2EAP_SEX_AGE_RT_A` and materialized; rerun or repair stale diagnostics. |
| 2 | `fred:WUXIASHADOWRATE` | 2 | High with key | Fetch with `FRED_API_KEY`. |
| 3 | `fred:M1204AUSM363SNBR` | 2 | High with key | Fetch historical FRED/NBER money series with `FRED_API_KEY`. |
| 4 | `ilostat:ILMS_wages` | 2 | Medium | Informal wage token; try fetch only after confirming ILO indicator code or add alias. |
| 5 | `un_comtrade:HS72_HS76_HS25_HS31` | 2 | Low | Comtrade fetcher/key blocked; CBAM product family. |
| 6 | `un_comtrade:unique_hs6_products` | 2 | Low | Comtrade HS6 product lines needed; WITS HHI is not a count substitute unless a benchmark-only redesign is accepted. |
| 7 | `un_comtrade:product_lines` | 2 | Low | Comtrade/BACI product-line spine needed. |
| 8 | `bls:LAUST010000000000003` | 2 | High | Already materialized via BLS LAU state unemployment; rerun/alias stale diagnostics. |
| 9 | `fred:UNRATE` | 2 | High | Already materialized; rerun stale diagnostics. |
| 10 | `fred:FEDFUNDS` | 2 | High | Already materialized; rerun stale diagnostics. |
| 11 | `bls:LNS11300000` | 2 | High | Already materialized; rerun stale diagnostics. |
| 12 | `fred:STTMINWGCA` | 2 | High | Already materialized; rerun stale diagnostics. |
| 13 | `boj:money_stock_m2` | 1 | Medium manual | BOJ manual CSV/XLS drop, then fetch. |
| 14 | `boj:CPI` | 1 | Medium manual | BOJ manual drop, then fetch. |
| 15 | `boj:bond_yields_10y` / `boj:bond_yields_30y` | 2 total | Medium manual | BOJ manual drop, then fetch each series. |
| 16 | `ecb:FM.*.MRR_FR.LEV` | 3 total | High alias | Alias `_FR` policy-rate shorthands to fetcher/storage `_RT` equivalent where appropriate. |
| 17 | `ecb:IRS.M.DE` | 1 | High alias | Fetcher shortcut exists; runner storage alias missing for `MIR__M.DE.B.A2A.A.R.A.2240.EUR.N`. |
| 18 | `eurostat:sts_inppd_q` | 1 | High | Real Eurostat dataset code; fetch directly. |
| 19 | `imf:WEO.NGDP_RPCH` | 1 | High alias | Strip `WEO.` prefix to existing `imf:NGDP_RPCH`. |
| 20 | `imf:BFOAFA` | 1 | Medium manual | BOP/IIP series; use `imf_ifs` manual-drop and bridge `imf:BFOAFA` to `imf_ifs:BFOAFA`. |
| 21 | `bls:CES1021100001` | 1 | Medium-high | Generic BLS API series; key recommended. |
| 22 | `bls:OEUM000000000000000001` | 1 | Medium-high | Generic BLS API series; key recommended. |
| 23 | `fred:IRLTLT30JPM156N` | 1 | High with key | Fetch FRED Japan 30-year long-term rate if series is live. |
| 24 | `fred:FRBATLWGT12MMUMHWGO` | 1 | High with key | Fetch FRED series if live. |
| 25 | `world_bank_wits:product_concentration` | 1 | Medium alias | Candidate benchmark alias to `wits:export_product_hhi_wits`, but only for concentration outcome, not product counts. |
| 26 | `un_comtrade:export_product_concentration` | 1 | Medium alias | Candidate benchmark alias to WITS HHI for Theil/HHI-style concentration sensitivity. |
| 27 | `world_bank_wits:weighted_mean_applied_tariff` | 1 | Low | True WITS tariff fetcher needed; HHI does not help. |
| 28 | `world_bank_wits:import_value` | 1 | Low | WITS or Comtrade trade-flow fetcher needed. |
| 29 | `imf:reer` / `imf_weo:reer` | 1 | Low-medium alias | WEO fetcher does not document REER; likely bridge to BIS `WS_EER` or another REER source, not IMF WEO. |
| 30 | `unctad:World`, `unctad:FDI`, `unctad:trade_indicators`, `unctad:commodity_price_indices` | 0 current / 4+ spec refs | Low-medium | Current UNCTAD fetcher supports only `US.FDI`, `US.FDIstock`, `US.TradeMerchTotal`, `US.TradeServ`, `US.GVCParticipation`; source tokens need aliasing and bulk URL repair. |

## WITS / Comtrade / UNCTAD Status

WITS HHI is now real local data:

- Token: `wits:export_product_hhi_wits`
- Vintage: `data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet`
- Manifest: `data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json`
- Coverage: 4,669 exporter-year rows, 207 reporter ISO3s, 1988-2022.
- Schema: `country_iso3`, `year`, `value`, `number_of_products`, `classification`, `partner_iso3`, `product_cluster`.
- Meaning: higher `value` means more concentrated product exports; rows are exporter-to-world (`PartnerISO3 == WLD`).

Implications:

- Ready as a benchmark product-concentration outcome.
- Not a substitute for WITS tariffs, import values, export values, or bilateral partner-product flows.
- Not a full substitute for Comtrade/BACI product lines; it cannot produce Theil, top-product shares, RCA, HS6 counts, commodity shares, or manufacturing basket shares from raw product lines.
- The runner can load `wits:export_product_hhi_wits` from `data/vintages/wits`, but `wits` / `world_bank_wits` is still not a ready fetcher in `publishers.yaml`. `scripts/fetch.py wits ...` will not dispatch until a publisher/fetcher entry exists.

Alias candidates after WITS HHI:

| Existing token | Candidate bridge | Caveat |
| --- | --- | --- |
| `world_bank_wits:product_concentration` | `wits:export_product_hhi_wits` | Good benchmark if the outcome is concentration. |
| `un_comtrade:export_product_concentration` | `wits:export_product_hhi_wits` | Good benchmark only for concentration, not Theil from raw shares. |
| `un_comtrade:export_product_diversity` | `wits:export_product_hhi_wits` with sign/inversion documented | Needs design approval because HHI is concentration, not diversity. |
| `un_comtrade:unique_hs6_products` | no direct bridge | HHI file has `number_of_products`, but runner currently loads only `value`; a derived series is needed if product counts matter. |
| `world_bank_wits:weighted_mean_applied_tariff` | no bridge | Needs WITS tariff source. |
| `world_bank_wits:import_value` / `export_value_constant_usd` | no bridge | Needs WITS/Comtrade trade-flow source. |

Comtrade status:

- `un_comtrade` is registered in `publishers.yaml` as `status: pending`, `auth_required: true`, `auth_env_var: UN_COMTRADE_KEY`.
- No `data/fetchers/un_comtrade.py` exists.
- No current `data/vintages/un_comtrade/` directory is visible.
- Current high-pressure tokens are product-family values/volumes for CBAM, product lines, unique HS6 products, product concentration, export diversity, and sector export values.

UNCTAD status:

- `data.fetchers.unctad` is ready and supports only `US.FDI`, `US.FDIstock`, `US.TradeMerchTotal`, `US.TradeServ`, `US.GVCParticipation`.
- Previous roundup logged 404 failures for all five supported UNCTAD bulk downloads, so this is not a clean ready fetch until URLs are repaired or manual fallback is added.
- Current specs cite unsupported tokens such as `unctad:World`, `unctad:FDI`, `unctad:trade_indicators`, and `unctad:commodity_price_indices`.

## Ready Fetches

Ready once credentials/manual files are satisfied:

```sh
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred WUXIASHADOWRATE
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred M1204AUSM363SNBR
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred IRLTLT30JPM156N
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred FRBATLWGT12MMUMHWGO
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred CAPUTLB00004S
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred M14M
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred BAMLC0A0CMTRIV
FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred HHDFA
```

```sh
BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls CES1021100001
BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls OEUM000000000000000001
BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls LAU_state_teen_employment_population_ratio_panel
```

The last BLS command is a desired panel name, but current `LAU_PANEL_SPECS` does not define a teen EPOP panel. It needs a fetcher extension or an alias to an existing valid BLS series before it will work.

```sh
python3 scripts/fetch.py eurostat sts_inppd_q
python3 scripts/fetch.py ecb IRS.M.DE
python3 scripts/fetch.py ecb 'FM.M.U2.EUR.4F.KR.MRR_FR.LEV'
python3 scripts/fetch.py imf GGX_NGDP
python3 scripts/fetch.py imf GGSB_NPGDP
python3 scripts/fetch.py imf NGDP_RPCH
python3 scripts/fetch.py ilostat EMP_TEMP_SEX_ECO_NB_E
```

Manual-drop commands after placing the relevant files:

```sh
python3 scripts/fetch.py boj money_stock_m2
python3 scripts/fetch.py boj CPI
python3 scripts/fetch.py boj bond_yields_10y
python3 scripts/fetch.py boj bond_yields_30y
python3 scripts/fetch.py boj flow_of_funds_jgb_holdings
python3 scripts/fetch.py boj inflation_expectations_household_survey
python3 scripts/fetch.py imf_ifs BFOAFA
```

## Alias / Source-Token Issues

High priority aliases/bridges:

| Source token | Proposed resolution | Expected current unlocks |
| --- | --- | ---: |
| `ilostat:unemployment_rate` | Already bridges to `ilostat:UNE_2EAP_SEX_AGE_RT_A`; rerun stale cards. | 3 |
| `imf_pcps:POILBRE` | Already materialized; rerun stale cards. | 2 |
| `imf_pcps:Primary` | Already aliases to `imf_pcps:PALLFNF`; rerun after confirming load. | 1 |
| `imf:WEO.NGDP_RPCH` | Bridge to `imf:NGDP_RPCH`. | 1 |
| `imf_weo:reer` / `imf:reer` | Do not fetch as WEO unless DataMapper confirms it; likely bridge to BIS `WS_EER` or an IFS/manual REER source. | 1 |
| `imf:BFOAFA` | Bridge to `imf_ifs:BFOAFA` after manual IMF IIP/BOP CSV drop. | 1 |
| `ecb:IRS.M.DE` | Bridge to stored `ecb:MIR__M.DE.B.A2A.A.R.A.2240.EUR.N`, or fetch through ECB shortcut and then add runner alias. | 1 |
| `ecb:FM.B/D/M.U2.EUR.4F.KR.MRR_FR.LEV` | Bridge `_FR` shorthands to `FM__D.U2.EUR.4F.KR.MRR_RT.LEV` or the correct ECB policy-rate key. | 3 |
| `ecb:terms_of_trade_index` | Not an ECB-native token; bridge to WDI `NE.TRM.TRAD.XD.WD` or Eurostat terms-of-trade dataset after design check. | 1 |
| `world_bank_wits:product_concentration` | Bridge to `wits:export_product_hhi_wits` for benchmark concentration only. | 1 |
| `un_comtrade:export_product_concentration` | Bridge to `wits:export_product_hhi_wits` for benchmark concentration only. | 1 |
| `unctad:FDI` / `unctad:World` | Likely bridge to `unctad:US.FDI` only if the UNCTAD bulk URL is repaired; otherwise WDI FDI already covers the fallback in cited specs. | 0 current / 4+ spec refs |
| `fred:HHDFA (USA)` | Strip country qualifier before fetch/load: `fred:HHDFA`. | 1 |
| `fred:state_unemployment_rate (LAUS)` | Not a FRED series id; map to BLS LAU or a curated state panel. | 1 |

## Credential Constraints

- FRED: hard requirement, `FRED_API_KEY`.
- BLS: fetcher allows no-key single pulls, but a key is needed for practical state/panel fanout. Campaign planner currently blocks if `BLS_API_KEY` is absent.
- UN Comtrade: `UN_COMTRADE_KEY` plus a new fetcher are both required.
- IMF IFS/BOP/AREAER: no public API in the current fetcher. Requires signed-in manual CSV/XLSX export into `data/manual/imf_ifs/`.
- WITS tariff/product lines: no ready local fetcher. Prior plan treats this as a staged metadata-smoke/data-smoke source, possibly registration or bulk-download workflow.

## Manual Drops

- BOJ: place per-series CSV/XLS/XLSX files in `data/manual/boj/`, then run `python3 scripts/fetch.py boj <series_id>`. Because the fetcher currently picks the latest file under the directory, stage one BOJ source file at a time or harden the fetcher before batch operation.
- IMF IFS: place the relevant IMF bulk export in `data/manual/imf_ifs/`, then run `python3 scripts/fetch.py imf_ifs <series_id>`.
- WITS HHI: already present locally. Future WITS tariff/product-line files should not be treated as this same HHI vintage.
- UNCTAD: if bulk URL repair fails again, add a manual-drop path for supported dataflows before treating `unctad:*` as ready.

## Top 20 Fetch / Alias Batch

These are future commands/edits; none were executed in this lane. Expected unlocks mean current missing-token blockers removed if the fetch/alias succeeds, not guaranteed hypothesis graduation.

| Rank | Batch item | Exact future command or edit | Expected unlocks | Notes |
| ---: | --- | --- | ---: | --- |
| 1 | Clear stale ILO unemployment | Existing bridge: `ilostat:unemployment_rate -> UNE_2EAP_SEX_AGE_RT_A`; rerun `python3 scripts/run_panel_fe.py inflation_cost_push_distributional_conflict_eurozone_2021_2024 --force`, `python3 scripts/run_panel_fe.py qe_financialisation_minsky_channel_2008_2021 --force`, `python3 scripts/run_panel_fe.py zlb_state_dependent_multiplier_pk_framing --force` | 3 | No data fetch needed. |
| 2 | Fetch FRED shadow rate | `FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred WUXIASHADOWRATE` | 2 | Blocks post-Covid/Fed cycle specs. |
| 3 | Fetch FRED historical money series | `FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred M1204AUSM363SNBR` | 2 | Great Depression monetary specs. |
| 4 | Resolve ILO wage token | No exact fetch command until the ILO indicator is identified; add an alias for `ilostat:ILMS_wages`, then run `python3 scripts/fetch.py ilostat <resolved_ILO_wage_indicator>` | 2 | Do not blindly trust informal token. |
| 5 | Add WITS HHI concentration bridge | Add bridge for `world_bank_wits:product_concentration -> wits:export_product_hhi_wits` | 1+ | Benchmark only. |
| 6 | Add Comtrade concentration bridge | Add bridge for `un_comtrade:export_product_concentration -> wits:export_product_hhi_wits` | 1+ | Benchmark only; not raw Theil. |
| 7 | Add IMF WEO prefix bridge | Add bridge `imf:WEO.NGDP_RPCH -> imf:NGDP_RPCH` | 1 | `NGDP_RPCH` already materialized. |
| 8 | Fetch IMF expenditure | `python3 scripts/fetch.py imf GGX_NGDP` | 1 | Also consider alias from `GGXG_NGDP` if DataMapper confirms code. |
| 9 | Fetch IMF structural balance | `python3 scripts/fetch.py imf GGSB_NPGDP` | 1 | If DataMapper rejects, move to IMF manual/drop or WEO code correction. |
| 10 | Fetch IMF IIP/BOP assets | After manual CSV drop: `python3 scripts/fetch.py imf_ifs BFOAFA` | 1 | Also bridge `imf:BFOAFA -> imf_ifs:BFOAFA`. |
| 11 | Fetch ECB German loan rate | `python3 scripts/fetch.py ecb IRS.M.DE` | 1 | Better still: add runner alias to existing MIR storage id. |
| 12 | Alias ECB MRR `_FR` tokens | Bridge `ecb:FM.*.MRR_FR.LEV` to the correct `_RT` key/storage. | 3 | Avoid duplicate ECB fetches if existing `FM__D...MRR_RT...` is acceptable. |
| 13 | Fetch Eurostat producer prices | `python3 scripts/fetch.py eurostat sts_inppd_q` | 1 | Real dataset code. |
| 14 | Fetch FRED Japan 30y rate | `FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred IRLTLT30JPM156N` | 1 | Japan fiscal/monetary spec. |
| 15 | Fetch FRED Atlanta wage tracker | `FRED_API_KEY=$FRED_API_KEY python3 scripts/fetch.py fred FRBATLWGT12MMUMHWGO` | 1 | Fed 2022 lag spec. |
| 16 | Fetch BLS clean-energy/mining employment | `BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls CES1021100001` | 1 | Generic BLS series path. |
| 17 | Fetch BLS OEWS generic series | `BLS_API_KEY=$BLS_API_KEY python3 scripts/fetch.py bls OEUM000000000000000001` | 1 | Validate series id first if BLS rejects. |
| 18 | BOJ M2 manual drop | Drop BOJ M2 file, then `python3 scripts/fetch.py boj money_stock_m2` | 1 | Stage one BOJ file at a time. |
| 19 | BOJ yield manual drops | Drop yield files, then `python3 scripts/fetch.py boj bond_yields_10y` and `python3 scripts/fetch.py boj bond_yields_30y` | 2 | Japan debt-sustainability spec. |
| 20 | Comtrade/WITS product-line spine | No fetch command yet; implement `data/fetchers/un_comtrade.py` and require `UN_COMTRADE_KEY` before running the planned smoke commands. | 6+ current, 30+ future | Highest long-run yield, not ready for a data fetch today. |

## Blocker Summary

- True fetch-ready but credentialed: FRED queue and most BLS generic pulls.
- True fetch-ready without credentials: Eurostat real dataset codes, ECB valid flow/key shortcuts, ILOSTAT real indicator codes, IMF WEO/PCPS supported codes.
- Alias-first: ILO informal names, IMF `WEO.` prefix, ECB shortcut/storage ids, FRED tokens with country qualifiers, UNCTAD aliases, WITS/Comtrade concentration-to-HHI benchmark mappings.
- Manual-drop: BOJ and IMF IFS/BOP/AREAER.
- Fetcher-needed: UN Comtrade product lines, WITS tariff/trade-flow data, WITS product-line exports, BACI HS6.
- Not solved by WITS HHI: tariffs, import/export values, HS6 product counts, top-product shares, RCA, Theil from raw product shares, and CBAM product-family values/volumes.
