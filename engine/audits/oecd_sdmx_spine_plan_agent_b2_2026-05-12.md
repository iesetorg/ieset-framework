# OECD SDMX Data Spine Plan - Group 2 / Agent B2

Date: 2026-05-12

Scope: inspect the current OECD fetcher and local OECD vintages, then define a concrete implementation path for STAN, Revenue, and Fossil support discovery without requiring network success.

## Local Findings

- `data/fetchers/oecd.py` already has the current SDMX 2.1 base URL, CSV transport with `format=csvfilewithlabels`, a best-effort live dataflow catalogue resolver, and shortcut support.
- Existing `data/vintages/oecd/` contains OECD labour, distribution, prices, productivity, national accounts, migration, EPL, health, and SOCX vintages. It does not currently contain STAN, OECD tax/revenue, or OECD fossil/energy vintages.
- STAN support is partially available: `_OECD_SHORTCUTS` maps `STAN` and `STAN_VA` to `OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0`, and a separate local vintage exists at `data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet`.
- Revenue support is partially available: `_DSD_AGENCY` includes `DSD_TAX`, `DSD_TAX_WAGES_COMP`, and `DSD_TAX_CIT`; `_OECD_SHORTCUTS` maps `DSD_TAX` to `OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1`. Local non-OECD revenue coverage already exists via WDI, OWID, JST, and Heritage vintages.
- Fossil support is not currently an OECD fetcher shortcut. Local non-OECD fossil/energy coverage exists via OWID, WDI/World Bank, and EIA vintages. IEA fossil subsidy support is manual-drop oriented in `data/fetchers/iea.py`.
- `scripts/fetch.py` is already compatible with OECD SDMX fetches through `python3 scripts/fetch.py oecd <series> --key <key> --start <period> --end <period>`.

## Added Discovery Helper

Added `scripts/discover_oecd_sdmx_support_2026_05_12.py`.

The helper is local-only by default. It parses the OECD fetcher mappings with `ast`, scans local vintages, and reports hypothesis/script/manifest references for:

- `stan`
- `revenue`
- `fossil`

Verification command run successfully:

```bash
python3 scripts/discover_oecd_sdmx_support_2026_05_12.py --ref-limit 8
```

The current result classifies STAN and Revenue as mapped with some local supporting vintages, and Fossil as not locally supported through the OECD fetcher.

## Concrete Implementation Plan

1. Preserve the generic OECD fetcher contract.
   - Keep `data/fetchers/oecd.py` as the shared SDMX spine.
   - Do not create one-off OECD HTTP clients for STAN or Revenue unless the shared fetcher cannot express the required dataflow.
   - Continue writing raw fetched frames through `write_vintage` so every dimension column is preserved.

2. Normalize support discovery before adding shortcuts.
   - Use the local helper first:
     `python3 scripts/discover_oecd_sdmx_support_2026_05_12.py --ref-limit 20`
   - Then, only when network is available, probe exact dataflow IDs through the existing fetcher/catalogue path.
   - Treat network failures, 403s, 404s, and ZenRows 422s as discovery outcomes, not blockers.

3. STAN path.
   - First candidate: existing shortcut `STAN -> OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0`.
   - First smoke fetch:
     `python3 scripts/fetch.py oecd STAN --start 2015 --end 2024`
   - If too large, fetch only confirmed sector/value-added keys after inspecting columns from the existing `data/vintages/oecd_stan` parquet.
   - If `DF_STAN` is stale, use the dataflow catalogue resolver or official catalogue query to identify the replacement STAN/SDBS dataflow, then add only a narrow shortcut alias.

4. Revenue path.
   - First candidate: existing shortcut `DSD_TAX -> OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1`.
   - First smoke fetch:
     `python3 scripts/fetch.py oecd DSD_TAX --start 1990 --end 2024`
   - If the target is total tax revenue share rather than wage-tax indicators, catalogue-probe OECD Revenue Statistics dataflows before broadening `_OECD_SHORTCUTS`.
   - Keep WDI/OWID/JST revenue vintages as fallback or validation series; do not silently substitute them in OECD-namespaced manifests.

5. Fossil path.
   - Do not add an OECD fossil shortcut yet. The local fetcher has no verified OECD fossil dataflow alias, and existing fossil coverage is outside `data/vintages/oecd`.
   - Prefer current non-OECD vintages for fossil electricity/fuel exports and the IEA manual-drop path for fossil subsidies.
   - If OECD fossil support is required, catalogue-probe environment/energy dataflows first, then add a narrow alias only after a successful metadata or smoke fetch. Candidate command placeholder:
     `python3 scripts/fetch.py oecd 'OECD.ENV.EPI,DSD_GHG@DF_AIR_GHG,1.0' --start 1990 --end 2024`
     This is a discovery candidate, not a verified shortcut.

6. Add a small spine audit after each successful probe.
   - Record dataflow id, key, row count, columns, period bounds, vintage path, and failure mode if any.
   - Keep these audits unique and append-only under `engine/audits/`.

## Next Commands

```bash
python3 scripts/discover_oecd_sdmx_support_2026_05_12.py --ref-limit 20
python3 scripts/fetch.py oecd STAN --start 2015 --end 2024
python3 scripts/fetch.py oecd DSD_TAX --start 1990 --end 2024
```

Optional local schema inspection before network fetches:

```bash
python3 -c "import pyarrow.parquet as pq; p='data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet'; print(pq.read_table(p).schema)"
```

## Guardrails

- Do not require network success for planning.
- Do not modify existing dirty files from other agents.
- Do not treat WDI/OWID/JST/IEA fossil or revenue vintages as OECD vintages.
- Add OECD fetcher shortcuts only after a verified dataflow id is known.
