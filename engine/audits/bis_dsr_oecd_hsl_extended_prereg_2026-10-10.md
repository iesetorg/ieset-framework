# Blind preregistration: household debt-service burden and ten additional well-being measures

**Status:** design and exact key roster only; no selected OECD HSL numeric value, null mask, or observation status was opened. The registration files must be committed together before a distinct descendant source-lock commit. No result or source lock is in this package.

**Family:** `bis_dsr_oecd_hsl_extended_wellbeing_2026_10_10`. The shared exposure is the change from t-1 to t in the annual average of four BIS household-sector quarterly debt-service ratios. Ten distinct OECD How's Life measures change from t to t+1; adverse orientation makes positive beta a worsening. This is a descriptive calibration, with zero causal, policy, school, position, or featured credit. The four earlier BIS/HSL endpoints and older BIS macro tests were visible when choosing this batch. Local Bonferroni correction does not control the adaptive IESET archive search or establish an independent replication.

## Fixed outcomes and blind coverage

| Case | OECD measure / unit | Key-only pairs / countries | Material DSR-change rows / countries | Treatment years | Post-lock minimum complete pairs / countries |
| --- | --- | ---: | ---: | --- | ---: |
| `relative_poverty` | `1_4` Household disposable income below the relative income poverty line; `PT_POP` | 204 / 15 | 153 / 15 | 2004–2023 | 150 / 12 |
| `employment_rate` | `2_1` Employment rate; `PT_POP_Y25T64` | 357 / 17 | 268 / 17 | 2004–2024 | 265 / 14 |
| `longterm_unemployment` | `2_3` Long-term unemployment rate; `PT_LF` | 354 / 17 | 265 / 17 | 2004–2024 | 260 / 14 |
| `youth_neet` | `2_4` Youth not in employment, education or training; `PT_POP_Y15T24` | 311 / 16 | 237 / 16 | 2004–2023 | 230 / 13 |
| `paid_long_hours` | `2_7` Long hours in paid work; `PT_SAL` | 315 / 15 | 243 / 15 | 2004–2024 | 230 / 12 |
| `low_earnings` | `2_8_DEP` Full-time employees earning less than two-thirds of gross median earnings; `PT_SAL_FT` | 214 / 11 | 163 / 11 | 2004–2024 | 155 / 9 |
| `negative_health` | `5_2_DEP` Perceived health as negative; `PT_POP_Y_GE16` | 269 / 14 | 204 / 14 | 2004–2023 | 200 / 11 |
| `despair_deaths` | `5_3` Deaths from suicide, alcohol, drugs; `DT_10P5HB` | 309 / 17 | 233 / 17 | 2004–2023 | 230 / 14 |
| `lack_social_support` | `7_1_DEP` Lack of social support; `PT_POP_Y_GE15` | 323 / 17 | 239 / 17 | 2006–2024 | 240 / 14 |
| `physical_pain` | `11_3` Feelings of physical pain; `PT_POP_Y_GE15` | 323 / 17 | 239 / 17 | 2006–2024 | 240 / 14 |

The sorted CSV `data/pinned_evidence/bis_dsr_oecd_hsl_extended_2026_key_roster.csv` contains exactly 2979 rows and SHA-256 `a1a9a2df5bc58ae9d1d14a88d4527ea8c39a520dfce079e6c6aa6cbb12f553dd`. Entries require HSL exact keys at t and t+1, complete BIS quarterly keys at t-1 and t, and at least three key-only years per country. A row key is not an observed HSL value. The preflight accessed HSL dimensions and keys only; it read BIS exposure values to evaluate material changes and influence. Treatment-only residualized DSR variance had top-1% row shares 14.6–22.3%, largest-country shares 17.2–27.5%, and largest-year shares 12.2–17.9% across the ten fixed rosters. Two unregistered housing endpoints (`3_1` crowding and `3_3` cost overburden) were rejected at this exposure-only stage because their narrower 2010–2023 key rosters concentrated 30.9–32.3% in one country and 33.0–35.7% in one year. No HSL measured values or statuses informed that exclusion.

## Source custody and interpretation

- BIS exact raw file `data/vintages/bis/WS_DSR@2026-07-22T141212Z.parquet` SHA-256 `59cb6b2f260d3132f826a15ccf585a3016af8516c4d0c2197a5fda2c2916b3fd`; committed fetch manifest `data/manifests/fetch_run_2026-07-22T141212Z.yaml` SHA-256 `895761a2da3bd2554da4466becd7fa85837258ce80442c519362bb9d4c5eaea2`. BIS H-sector includes households and nonprofit institutions serving households, and cross-country levels are less comparable than within-country changes. [BIS DSR overview](https://data.bis.org/topics/DSR?m=6_380_671).
- OECD exact raw file `data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet` SHA-256 `ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db`; committed fetch manifest `data/manifests/fetch_run_2026-07-23T150922Z.yaml` SHA-256 `f8d2a682717c02832a2cf323fb5ea777139502e14987348859f3114042bece51`. The filename is an historical housing alias; the manifest source is `OECD.WISE.WDP,DSD_HSL@DF_HSL_CWB,1.1`. [OECD How's Life definitions](https://www.oecd.org/wise/oecd-well-being-database-definitions.pdf).
- Both whole manifests contain unrelated absolute paths; the later source lock must record only the two selected entries, manifest hashes, registration commit, and roster. Ignored raw Parquets are byte-pinned but not shipped by Git. No vintage substitution is permitted.

## Frozen estimator and verdict

At t and t+1, require finite selected HSL values in [0,100] for shares or [0,500] deaths per 100,000 for measure 5_3, with `OBS_STATUS` A or blank. BIS quarters must have actual-status A and be finite [0,100]; the treatment-only source has 1,836 selected A-status rows and no other selected statuses. Drop only invalid/incomplete exact-roster pairs, then economies with fewer than three complete pairs. Keep all valid exposure shocks; no trimming or winsorizing. A selected HSL status other than A/blank is invalid. The HSL status codes are read only after the source lock.

Fit one country/year fixed-effects OLS for each adverse-oriented forward outcome change on the prior annual DSR percentage-point change. Use country-cluster CR1 with small-sample correction and two-sided Student t(G−1). Require each case-specific complete-row/country and material-row/country floors in its YAML, full rank, finite positive clustered uncertainty, and no more than 30% of the country/year-residualized exposure variance in the top 1% of rows, one country, or one year. The complete-case influence gate is calculated after the source lock and cannot be changed.

All ten tests remain in one Bonferroni family with alpha 0.01 and two-sided p≤0.001 each, even when another is inconclusive. SUPPORTED requires adverse beta≥+0.25 outcome units per one DSR percentage point and p≤0.001; REFUTED requires beta≤−0.25 and the same p; any other estimable result is PARTIAL; any source/sample/influence/fit gate failure is INCONCLUSIVE. The `5_3` outcome unit is deaths per 100,000; other outcomes are percentage points. This is a practical threshold, not an effect-estimation guarantee. No secondary fit can upgrade the primary verdict.

## Overlap and limits

Existing strict HSL tests of this BIS exposure cover difficulty making ends meet (`1_5`), housing affordability (`3_2`), home warmth (`3_5`), and negative affect (`11_2`). Older BIS tests cover aggregate consumption, unemployment surge, property, and credit outcomes. The ten measures above are exact directed source/measure pairs absent from authored hypothesis specs at registration, but they share many countries, years, and upstream macro shocks. Employment rate and long-term unemployment are related to the older unemployment-surge case; they are distinct measured constructs, not independent confirmation. OECD HSL survey averages may pool years. Income, interest rates, recessions, demographics, and public policy jointly affect DSR and the outcomes. The country series cannot link debtors to outcome respondents; temporal ordering and fixed effects do not identify effects.

## Required chronology

1. Review and commit this audit, the ten YAML specs, ten steelmen, exact key roster, runner, and any synthetic tests in one **first-addition registration commit**, with no result artifact or source lock.
2. Run `scripts/run_bis_dsr_oecd_hsl_extended_2026.py --write-source-lock`; commit `data/pinned_evidence/bis_dsr_oecd_hsl_extended_2026.manifest.json` in a distinct descendant commit. The runner checks registration byte identity, source hashes, manifest entries, and the key-only roster before this step.
3. Only after the source-lock commit may `scripts/run_bis_dsr_oecd_hsl_extended_2026.py --run` open selected HSL values and statuses. Preserve every outcome including PARTIAL, REFUTED, and INCONCLUSIVE. Exact replay with `--verify` is required before public-index regeneration. No gate or estimator change after selected outcome access.
