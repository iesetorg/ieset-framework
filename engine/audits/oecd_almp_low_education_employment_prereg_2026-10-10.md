# Preregistration: public ALMP spending and low-education employment

**Family:** `oecd_almp_low_education_employment_2026_10_10` (one descriptive test). This registration is to be committed before a separate source lock and before any selected Eurostat employment values or null masks are opened. Preflight used only OECD treatment values, WDI control values, Eurostat schema and selector/country-year keys. Eurostat `lfsa_ergaedn` has no cell-status or method-break column in the pinned vintage. No source-lock or result is part of this registration package.

## Fixed question

Across the exact country-year roster, does an OECD public SOCX TP60 spending increase of at least **0.05 GDP percentage point** from `t−1` to `t` predict a greater change in the Eurostat low-education employment rate from `t` to `t+1` than a spending decrease of at least the same size? The indicator is annual, total citizenship, ISCED 0–2, both sexes, age 25–64, percent. Smaller spending changes form the stable category. This is a budget-share association, not programme participation or a treatment effect.

## Pinned sources and selection

| Role | Exact local vintage / SHA-256 | Fetch manifest / SHA-256 |
| --- | --- | --- |
| OECD SOCX ALMP | `data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet` / `93e7e29b24dc791baf22833ae5596b4a381a366ddd0d78499bf59f7b80786124` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` / `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| WDI GDP per person | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` / `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` / `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| Eurostat employment | `data/vintages/eurostat/lfsa_ergaedn@2026-04-30T125100Z.parquet` / `6bdae02133c40b7498922a0a1fa2b28d3e63fcde3fff3915353e87275c78edc3` | `data/manifests/fetch_run_2026-04-30T125203Z.yaml` / `9fb01a47d0598eb7d91de7765aea54a25f100c490d88b9414c6e8453a90d1df6` |

SOCX selector: `FREQ=A, MEASURE=SOCX, UNIT_MEASURE=PT_B1GQ, EXPEND_SOURCE=ES10, SPENDING_TYPE=_T, PROGRAMME_TYPE=TP60, PRICE_BASE=_Z, OBS_STATUS=A`; require finite values in `[0,10]` percent GDP at `t−1,t`. WDI selector: indicator `NY.GDP.PCAP.KD`, positive finite value and blank status at `t`; use its natural log. Eurostat selector: `freq=A, citizen=TOTAL, isced11=ED0-2, sex=T, age=Y25-64, unit=PC` and mapped national geography. The outcome file has only `freq,citizen,isced11,sex,age,unit,geo_code,period,value`; **only the first eight columns may be read in preflight**. Require exact keys at `t,t+1`, no duplicates, `t=2005–2018`, and at least five candidate years per country. Crosswalk `EL→GRC`, `UK→GBR`; aggregates and unmapped geographies are excluded.

Frozen key-only roster: `data/pinned_evidence/oecd_almp_low_education_employment_2026_key_roster.csv`, SHA-256 `0b6d3f7c6758641c29ba8e03006f08a0be44d60023ffc08c3710582eecf84445`. It contains **410 candidate pairs in 30 countries**. Treatment-only coding yields **78 increases in 28 countries**, **82 decreases in 24 countries**, and **250 stable rows**, across treatment years 2005–2018. After partialling each event indicator on the opposite indicator, log GDP per person, country and year effects, the top 1% of rows account for 10.17% of increase residual variation and 8.92% of decrease variation; the largest-country shares are 7.57% and 5.94%. These are upper-bound sample metrics because no Eurostat value or missingness mask was opened. The prior continuous-change candidate had concentrated 2020–21 exposure and is not this registered test.

## Frozen model and gates

After source lock, require both selected Eurostat rates finite in `[0,100]`. Drop a pair only for missing/invalid endpoints; then drop countries with fewer than five complete pairs. Do not trim by outcome magnitude, inspect flags absent from this vintage, interpolate, change years/countries, or substitute a source. The primary outcome is the rate at `t+1` minus its baseline at `t`, in percentage points. Regress it on mutually exclusive increase and decrease indicators, baseline rate at `t`, log real GDP per person at `t`, country effects, and treatment-year effects. The primary estimand is **βincrease − βdecrease**. Estimate OLS with country-cluster CR1 standard errors; use a two-sided Student `t` test with `G−1` country degrees of freedom and a 99% confidence interval. Individual event coefficients and stable-reference comparisons cannot determine the verdict.

Require at least **300 complete pairs/25 countries**, five complete years per retained country, **50 increase events/15 countries**, **50 decrease events/15 countries**, full rank, at least 25 clusters, finite positive clustered uncertainty, and no more than **30%** of either event indicator's residual squared variation in the top 1% of rows or in one country (partialling on the opposite event, baseline rate, log GDP per person, country and year effects on the complete sample). A failed gate is INCONCLUSIVE. Otherwise the single-test family alpha is **0.01**: SUPPORTED requires contrast ≥**+0.5 employment-rate point** and two-sided p≤0.01; REFUTED requires contrast ≤**−0.5 point** and p≤0.01; all other estimable results are PARTIAL. This symmetric rule was chosen before outcome access. No diagnostic or alternative window can change it.

The row, country, and event floors guard against near-empty estimation; they do not guarantee statistical power for a 0.5-point contrast. An imprecise fit remains PARTIAL rather than being promoted by a different window or cutoff.

## Prior work and limits

A direct scan of authored hypothesis YAML found no exact OECD SOCX `DSD_SOCX` × Eurostat `lfsa_ergaedn` source pair. Prior records include OECD ALMP versus migrant unemployment and low-education unemployment, a business-R&D versus tertiary-employment study using the same Eurostat dataflow, and other family-support/employment screens. This is a new measured pairing and estimand, not independent replication of the broader ALMP literature or a school prediction. The local alpha does not adjust for all exploratory IESET work.

ALMP spending can be countercyclical, and spending divided by GDP can jump as GDP falls. Adult employment may change with classification, survey methods, macro conditions, and workforce composition. The pinned Eurostat file lacks cell-level quality/break flags. Baseline-rate adjustment can be sensitive to regression to the mean. No result receives causal, programme-effect, policy-score, school-score, position, or featured credit.

## Required sequence

1. Commit this audit, YAML specification, steelman, exact key roster, guarded runner, and synthetic tests together, with no measured result or source lock.
2. Copy the three exact pinned source files and their fetch manifests byte-for-byte if absent, then use the guarded `--lock` action. Commit its narrow source-lock JSON in a **separate descendant commit**, with no result.
3. Only then may `--run` load Eurostat values. Publish both null and estimable outcomes faithfully; `--verify` must independently replay every generated artifact before any public index is refreshed.
