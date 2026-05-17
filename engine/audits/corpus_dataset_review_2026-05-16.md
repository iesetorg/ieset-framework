# IESET Corpus And Dataset Review - 2026-05-16

Scope: one-pass review of the IESET hypothesis/evidence corpus, movement corpus, and local dataset vintages. This is a planning and QA artifact; it does not change hypotheses, verdicts, scoreboards, or any external reply/posting runtime.

Boundary: Reply Guy is a separate runtime/app and should remain outside the IESET repository. IESET may expose evidence artifacts that external tools read, but it should not contain Reply Guy code, queues, logs, approvals, training corpora, launch agents, or posting workflows.

## Inventory Snapshot

### IESET Evidence Corpus

- Hypothesis YAML files: 1,628 total; 1,605 are tracked by the current runnability audit.
- Runnability-tracked specs: 1,605.
- Existing run directories: 1,607.
- Runnability state from `engine/runnability.report.md`:
  - `READY`: 1,467
  - `NEEDS_DATA`: 137
  - `NEEDS_TEMPLATE`: 1
  - `HAS_RUN`: 1,605
- Topic concentration:
  - Growth: 418 YAML files
  - Labour: 198
  - Monetary: 164
  - Trade: 146
  - Regulatory: 132
  - Fiscal and distribution: 100 each
  - Resource rents remains tiny: 3

### Run Corpus

All inspected run directories had diagnostics and result cards. The verdict mix is useful but still needs QA before public scoring:

- `PARTIAL`: 742
- `SUPPORTED`: 430
- `REFUTED`: 133
- Inconclusive/data-pending variants: about 187
- Other/format-fragile verdict labels remain and should be normalized before downstream automation.

Important quality note: the third 40-run wave reported 24 of 40 packets with `no_input_vintages_recorded`. Those results may be useful internally, but they should stay out of public/scoreboard lanes until provenance is repaired.

### Movement Corpus

- Movement YAML files: 645.
- All 645 inspected movements now have `axes_summary`.
- All 645 have at least one `position_alignments` entry.
- 279 have `outcome_hypotheses`; this is the next main coverage gap.
- Position alignment counts are broad enough to support serious movement-panel tests:
  - `aligned`: 1,287
  - `partially_aligned`: 1,254
  - `opposed`: 886
- Most common country coverage includes USA, Italy, UK, Japan, Israel, Thailand, India, Brazil, Argentina, Germany, France, Colombia, Poland, Netherlands, Greece, Nigeria, and Korea.

### Dataset Vintages

There are 68 parquet publisher directories under `data/vintages`, including alias directories. The largest useful families:

- WDI / World Bank aliases: 455 files, 178 variables, 1960-2025, 261 country codes.
- Eurostat: 81 files, very large row count, but many tables need country/year normalization before global-panel use.
- BIS: 31 files, 1947-2025, strong for credit, rates, debt-service, cross-border claims, and REER.
- OECD: 36 files, large tables but high missing-series pressure and SDMX harmonization cost.
- Movements: 107 derived movement vintages, 1800-2026, 272 country codes.
- PWT: 18 files, 1950-2019, now includes `rgdpo_pop`.
- WGI: 32 files, 1996-2024, core institutional controls.
- WID, FAOSTAT, ILOSTAT, CEPII, UNDP HDI, Fraser EFW, Heritage IEF, Chinn-Ito, Laeven-Valencia, JST, and derived panels are all locally useful.

Fetcher registry state:

- Publisher entries: 163
- `ready`: 80
- `pending`: 83

Top blocker publishers from runnability:

- `boj`
- `ilzetzki_reinhart_rogoff`
- `wipo`
- `world_bank_wits`
- `dates`
- `ilo`
- `un_comtrade`
- `unctad`
- `iea`
- `barro_lee`

Top missing-series pressure:

- OECD: 66 mentions
- ECB: 18
- BLS: 13
- PWT: 11
- IMF: 11
- OECD PMR: 10
- FRED/WDI: 8 each

The inconclusive-campaign dry run found 405 unresolved unique publisher/series pairs. The top immediately queued repair targets were OECD health/immigration/earnings/tax series, WDI poverty and business-permit series, ILOSTAT wages, V-Dem corruption, WHO BMI/alcohol, BOE gilt series, and BOJ CPI/yield series.

## Main Diagnosis

The repo has a large, increasingly useful economics evidence base: hypotheses, movement coding, derived movement vintages, and many official-data panels. The weak point is not another broad run wave. The weak point is evidence routing, provenance repair, and movement/event coding that lets tests answer concrete historical claims.

The dataset side is good enough for daily hypothesis production, but public-grade score movement should be more selective. The best frontier is not more broad FE runs; it is higher-quality data replacement, derived joins with manifests, and movement/event coding that lets tests answer concrete historical claims.

## What Should Happen Next

### 1. Build A Claim-to-Receipt Export Layer

IESET should export clean, public-safe evidence packets that external tools can consume. Create a curated routing layer for common debate claims:

- rent control and housing supply
- zoning/planning restrictions
- minimum wage and low-wage employment
- wealth taxes and capital flight/evasion
- public spending and growth
- debt/deficits/inflation
- socialism/Marxist-Leninist country outcomes
- Nordic/social-democratic claims
- Spain/France/Germany comparative claims
- energy prices, deindustrialization, and climate policy
- trade openness and export diversification

Each route should have:

- allowed hypothesis IDs
- verdict-sensitive public wording
- allowed verbatim stats
- disallowed overclaims
- fallback mechanism argument when evidence is partial or blocked
- a machine-readable export format that lives in IESET, while any posting/runtime consumer lives elsewhere

### 2. Push Movement Corpus From Labels To Tests

The movement backfill succeeded on alignment coverage. The next gap is outcome hypotheses:

- Current outcome coverage: 279 / 645 movements.
- Target: 500+ movements with at least one outcome hypothesis.
- Priority: Marxist-Leninist/state-socialist, resource-statist, developmentalist, market-liberal reform, welfare-state expansion, and planning/regulatory regimes.

Use movement vintages for daily tests, but do not score broad proxy results without QA.

### 3. Dataset Repair Priorities

Highest-leverage dataset work:

1. BOJ macro/financial series: unlocks Japan monetary/debt hypotheses.
2. OECD SDMX aliases: unlocks many currently blocked OECD runs.
3. WDI alias cleanup: many are small source-name/series-name misses.
4. PWT aliases: `rgdpo_pop`, `rconna`, `rnna`, `rgdpo_emp`.
5. WGI aliases: `rule_of_law`/`RQ.EST` source-name consistency.
6. UN Comtrade or UNCTAD product exports: replace broad WDI export-HHI proxy with real product-level diversification.
7. WIPO/OECD patents: strengthen innovation/productivity claims.
8. World Bank WITS: tariff and trade-liberalization tests.
9. ILOSTAT wages/earnings: labour-market and minimum-wage tests.
10. Manifest repair for old runs with missing input-vintage provenance.

### 4. Keep The Automations Split

The right automation architecture is now:

- Data backfill: fetch/land data, no hypothesis scoring.
- Movement-policy 40/day: capped daily evidence production and QA.
- Dataset-upgrade scout: find stale runs made obsolete by bigger/better data.
- External consumer/export refresh: IESET can refresh evidence packets, but live reply queues and posting workflows stay outside this repo.

These should stay separate. Mixing live posting, dataset repair, and score movement in one agent will make failures hard to diagnose.

## Recommended Next 7-Day Build Order

1. Create the first claim-to-receipt export layer for 10 common debate topics.
2. Run the dataset-upgrade scout once manually and inspect its queue.
3. Build a product-level export diversification plan using UN Comtrade/UNCTAD/BACI.
4. Raise movement `outcome_hypotheses` coverage from 279 to 350 as the next batch.
5. Repair provenance for high-value old runs with missing input-vintage records.
6. Run one controlled movement-policy 40/day batch with no scoreboard changes.
7. Document the external-consumer contract: IESET exports evidence; separate apps consume it.

## Bottom Line

The corpus is now strong enough to be dangerous in a good way, but the next leap is discipline: routing tables, provenance repair, external-consumer exports, and smaller high-confidence public evidence packets. IESET can already generate evidence. The next task is making sure every exported claim is visibly tied to the right evidence and every automated run knows when to stop.
