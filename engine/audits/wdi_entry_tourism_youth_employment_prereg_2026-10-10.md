# Prospective two-test registration: WDI business entry and inbound tourism to OECD youth employment

**Family ID:** `wdi_entry_tourism_oecd_youth_employment_2026_10_10`

**Status at this registration:** source hashes, treatment values, and OECD keys/dimensions/status examined; **no selected OECD outcome values, signs, null masks, or fits opened**.

**Credit rule:** descriptive calibration only. Every verdict has zero causal, policy, school-score, and featured credit.

## Fixed questions and source definitions

1. `wdi_new_business_registrations_oecd_youth_employment_forward_2026`: Does the annual log change in WDI `IC.BUS.NREG` new formal limited-liability registrations from `t−1` to `t` positively predict the OECD youth employment-to-population rate change from `t` to `t+1`?
2. `wdi_tourism_arrivals_oecd_youth_employment_forward_2026`: Does the annual log change in WDI `ST.INT.ARVL` inbound arrival **trips** from `t−1` to `t` positively predict that same one-year-forward OECD youth employment-rate change?

Both WDI series are source-provided annual counts assembled from national administrative or survey sources; the vintage does not certify each country-year cell as independently observed. The OECD ratio is based on national labour-force surveys: employed people aged 15–24 divided by population aged 15–24. The WDI registration measure is not net firm formation, active establishments, sole proprietors, informal firms, or employment. The tourism measure is not unique travelers, domestic tourism, or visitor spending; its national source and visitor definition can differ. These are exposure associations, not identified interventions. [World Bank registrations](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IC.BUS.NREG), [World Bank arrivals](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/ST.INT.ARVL), [OECD employment rate](https://www.oecd.org/en/data/indicators/employment-rate.html).

## Frozen raw custody and exact selectors

| Role | Relative raw path | SHA-256 | Fetch manifest and SHA-256 |
| --- | --- | --- | --- |
| Outcome | `data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet` | `ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae` | `data/manifests/fetch_run_2026-07-23T151302Z.yaml`, `4952688fa8fbf62df91c20409bf4180b75977bc638bb33e2a00a267b3053b601` |
| Registrations | `data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet` | `213a70ca7b1b8259d58f3a3b9e90b9fb84cce3f77b881667f8811a71d25e75ae` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml`, `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| Arrivals | `data/vintages/world_bank_wdi/ST.INT.ARVL@2026-05-05T203952Z.parquet` | `1336df1cce2b3a2e784f917caa9487753d4cf53ad4ec65e5ea2fb045b0d41da5` | same WDI fetch manifest and hash |

The runner validates whole-file SHA-256 and the exact selected publisher, series ID, relative parquet path, and entry hash inside each original manifest. The later narrow source lock contains only these three selected manifest entries and no home-directory paths. The currently assigned isolated worktree has both fetch manifests but lacks the three raw parquet files; byte-identical copies must be supplied to it and rehashed before the source-lock commit. Missing or mismatched sources stop the study.

WDI treatment selector: `indicator_id=IC.BUS.NREG` or `ST.INT.ARVL` as appropriate, nonblank three-letter country ISO3, exact annual `year`, unique country-year key, positive finite count at both `t−1` and `t`. Blank WDI `obs_status` is an observed property of both pinned treatment files; it cannot identify treatment method breaks. No country-level rate denominator or external smoothing is introduced.

OECD outcome selector: `MEASURE=EMP_RATIO`, `UNIT_MEASURE=PT_POP_SUB`, `SEX=_T`, `AGE=Y15T24`, `LABOUR_FORCE_STATUS=EMP`, exact annual `period`, and **`OBS_STATUS=A` at both `t` and `t+1`**. Require `REF_AREA` in the 53 frozen three-letter country codes declared by the runner; exclude OECD/EU/G7 aggregates and `DEU_F`. The selected normal-status slice has 1,930 country-year keys across 53 countries, without duplicate keys. The raw selected slice also has 2 `B` time-series-break rows and 22 unlabeled-status rows, all excluded. `A` is a source status, not an assurance that the numeric outcome is nonmissing; numeric completeness is assessed only after the source-lock commit. No nearest-year join, forward fill, interpolation, alternate code, or substitute series is permitted.

## Frozen sample and exposure-only filters

- Treatment years `t=2007…2018`, pre-pandemic; the exact outcome endpoints are `t` and `t+1`. The 2007 start permits a 2006 registration baseline, and the 2018 end puts the forward endpoint in 2019. Country and year are matched exactly.
- `x_{c,t}=log(T_{c,t})−log(T_{c,t−1})`. The registrations test keeps `|x|≤0.4`; the arrivals test keeps `|x|≤0.3`. The caps were chosen using treatment values alone to remove extraordinary annual discontinuities; they may also remove real economic shocks and do not establish that smaller changes are error-free.
- A material change has `|x|≥0.1`. This category is a design floor, not an estimation subsample: all eligible small and zero changes remain in the regression.
- A country needs at least five eligible key-only treatment years before the roster, then at least five complete outcome pairs after unlocking.
- The committed key-only roster must be `data/pinned_evidence/wdi_entry_tourism_youth_employment_2026_key_roster.csv` with SHA-256 `b571b45b3a94765bf1661b97908670dac88980d8598d92c43e3fdeb74449f556`. Sorted `case_id`, treatment-year, country keys are immutable.

| Test | Frozen key-only pairs / countries | Treatment-only material pairs / countries | Minimum complete pairs / countries | Minimum material complete pairs / countries |
| --- | ---: | ---: | ---: | ---: |
| Registrations | 489 / 45 | 175 / 43 | 350 / 30 | 100 / 25 |
| Arrivals | 564 / 50 | 124 / 40 | 400 / 35 | 70 / 25 |

The complete and material floors are applied after the five-complete-year country rule. Failure is `INCONCLUSIVE`, never a favorable result. Selected outcome missingness remains unknown at registration.

## Estimator and verdict, fixed now

For each test, regress the one-year change in youth employment percentage points, `Y_{c,t+1}−Y_{c,t}`, on `x_{c,t}` plus country and treatment-year fixed effects. Use OLS, country-cluster CR1 covariance, and a two-sided Student t reference with `G−1` country degrees of freedom; report the matching **99.5% two-sided confidence interval** using the `t(0.9975, G−1)` critical value. No adaptive covariates, lags, windows, or sample trimming. The design must be full rank, with finite positive cluster standard error. On the complete fitted sample, residualized treatment variation must have at most **30%** of its squared sum in the highest-leverage 1% of rows and at most **20%** in any one country; failure is `INCONCLUSIVE`. Treatment-only preflight shares were 13.3%/8.1% for registrations and 22.7%/10.8% for arrivals, respectively; no outcome values entered these calculations.

The family has **two fixed tests** and **family alpha 0.01**, so each uses **two-sided Bonferroni p ≤ 0.005** even if the other test is inconclusive. For each test, `SUPPORTED` requires `beta ≥ +1.0` youth-employment percentage point per one-unit log treatment increase *and* p ≤ 0.005. `REFUTED` requires `beta ≤ −1.0` and the same p cutoff. Every other estimable result is `PARTIAL`. A 0.1 log increase corresponds to approximately 10.5% exposure growth, so this magnitude means at least 0.1 youth-employment percentage point for that change. The inference threshold and magnitude are not revised after results.

## Prior archive and interpretation boundary

An exact source-ID overlap screen of visible strict and older hypothesis YAML found neither new directed WDI treatment → OECD youth-employment pair. The existing `wdi_business_entry_rule_of_law_growth_panel` connects registrations to GDP growth; `business_freedom_employer_entry_employment_panel` connects business freedom to entry and employment; `oecd_youth_wage_gap_youth_employment` uses the OECD youth outcome with a wage-gap treatment. Existing Singapore, UAE, Dominican Republic, and other tourism/development hypotheses use arrivals or tourism but not this OECD youth outcome. These are thematic predecessors, so this family is not an independent archive-wide holdout and cannot multiply historical graduation credit.

Demand shocks, credit conditions, exchange rates, policy changes, migration, demography, registry digitization, travel collection rules, and reverse timing can jointly affect exposure and youth employment. WDI treatment status fields are blank and cannot screen method breaks. OECD labour-force-survey practice can change even among `A` rows. The selected outcome is a survey estimate; it is not an administrative count of youth jobs. Support establishes only the two measured forward associations under this frozen specification. The resulting records must carry zero causal, policy, school-score, and featured credit, irrespective of statistical verdict.

## Execution chronology

1. Commit this preregistration document, both specs and steelmen, runner, and key-only roster together. No measured result artifact is in that commit.
2. Supply the three raw files by byte-identical copy if absent, verify all SHA pins and selected manifest entries, generate the narrow source lock with `--write-source-lock`, and commit that lock separately after registration. The lock contains the registration commit ID.
3. Only then run `--run`, which first checks both commits and only afterward reads OECD numeric outcome values and their missingness. Preserve all `SUPPORTED`, `REFUTED`, `PARTIAL`, or `INCONCLUSIVE` outcomes.
4. Run `--verify` for exact replay, then commit measured artifacts in a third boundary. No push, merge, policy claim, or scoreboard credit follows automatically.
