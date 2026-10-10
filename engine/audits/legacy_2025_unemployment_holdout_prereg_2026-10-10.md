# Source-key audit and blind registration: 2025 unemployment follow-up

This audit reviewed the 203 legacy same-commit pairs with full vintage path/SHA references, focusing on the 22 whose surviving local raw source files have at least one later calendar-year key. The old specifications and run artifacts were visible. No selected 2023 or 2025 OECD unemployment values, null masks, status fields, coefficient, or verdict were opened here. Source-key counts are upper bounds on complete cases. No old hypothesis is relabeled or graduated by this registration.

## One prospective lead

The old `oecd_collective_bargaining_unemployment_nonpenalty` specification ends in 2022. Its manifest labels the same-commit run SUPPORTED, while the later diagnostics and result card label it PARTIAL. Neither can supply prospective credit. A 2023 OECD bargaining-coverage exposure and a separately preserved 2025 OECD LFS unemployment outcome allow a narrow out-of-time descriptive v2.

Key-only filters are OECD coverage `MEASURE=ERB` in 2023 and OECD LFS `MEASURE=UNE_RATE, SEX=_T, AGE=Y15T64, LABOUR_FORCE_STATUS=UNE` in both 2023 and 2025. Excluding the OECD aggregate yields exactly 26 reporter economies, frozen in `data/pinned_evidence/oecd_bargaining_unemployment_2025_temporal_holdout_v2_key_roster.csv` (SHA-256 `0160f69e5ff5a0995ba95da2d1dec1ace90aa251a07e1084414653591c81eebd`). All 26 selected 2023 exposure records have actual status A and finite percentages. Exposure-only values span 7.9–100.0 points, have a 70.1-point IQR, and the largest share of centered exposure variation is 0.0804. The 2024 exposure offers only 18 non-aggregate joint keys, so the frozen exposure year is 2023. The selected 2025 outcome remains unopened.

The single registered test estimates the 2023-to-2025 working-age unemployment change against 2023 bargaining coverage, adjusting for 2023 unemployment. It requires at least 24 complete countries, a 20-point exposure IQR, full rank, finite HC3 uncertainty, and frozen leverage/concentration limits. The one-sided 95 percent upper confidence bound must be at most +0.2 unemployment percentage point per ten coverage points to support the descriptive non-inferiority claim. A lower bound above that margin refutes it. Otherwise a method-valid run is PARTIAL; any gate failure is INCONCLUSIVE with no coefficient. There is no country or year fixed effect, causal/policy/school credit, or transferred old verdict.

## Pinned custody

| Role | Source file and SHA-256 | Fetch manifest and SHA-256 |
| --- | --- | --- |
| 2023 coverage | `data/vintages/oecd/OECD.ELS.SAE_DSD_TUD_CBC_DF_CBC_1.0@2026-05-01T071721Z.parquet`, `45010f706f77803e30cb98d9383e2f19ec54a23c119f693c875e124aa7441086` | `data/manifests/fetch_run_2026-05-01T071724Z.yaml`, `74d74d5cdc766624023d26fc3eec0eadf8f56efed52cfb30ff57c57b344db4d6` |
| 2023 baseline and 2025 unemployment | `data/vintages/oecd/DSD_LFS_DF_LFS_INDIC@2026-07-23T151216Z.parquet`, `ac58f9ea05eb07e0d4696a81334021120cd679f58847a2fb32dc70e06074e6ae` | `data/manifests/fetch_run_2026-07-23T151302Z.yaml`, `4952688fa8fbf62df91c20409bf4180b75977bc638bb33e2a00a267b3053b601` |

The old LFS vintage `DSD_LFS_DF_LFS_INDIC@2026-05-01T071721Z.parquet` has raw years through 2024, not 2025; its old manifest pins SHA-256 `46a244d6223b09908dd778a8125e383c853574f6d63b7daa03a83c329f31dd62`. The 2025 key is genuinely later than that source and outside the old fit, though the July LFS vintage may overlap other IESET work. The two new source files survive in the main IESET local raw store, which is ignored by Git and must be restored by hash into an isolated checkout before any run. This registration commit precedes a separate source-lock commit and outcome access.

## Why the other 21 later-year leads are not this test

The BIS real-property-price refresh has only 2026-Q1 as a new quarter. The proper quarterly real-index selector has 26 country keys before outcome-completeness review. At the corresponding 2023-Q1 credit-gap exposure, 20 countries have source keys but **zero** meet the archived high-gap threshold of 10 points. At 2024-Q1 only seven countries have household-DSR exposure keys. Policy-rate tightening has 20 matched exposure keys and only three episodes meeting the old two-point threshold. None supports the old 600–700-row panel floors, a country/year FE estimate, or a balanced binary comparison; only exposure values and outcome keys were read.

The 2026 ECB rate observation falls after the negative-rate intervention window; housing-inequality cells are not the intergenerational-mobility outcome. For the OECD 2025 LFS cases, the growth and Gini claims gain only a control, while the youth-wage-gap claim has 16 country keys with 2023 wages and 2025 youth employment (four with 2025 wages). The Poland 2017 retirement-age case has a later labour-force observation, but its claimed early-pension take-up is still incorrectly proxied by population and the 2017 causal contrast is not unlocked by one more post-event year. The remaining 2026 BIS property-price keys are controls, off-window observations, or components of broader claims whose other outcomes have not advanced. These are specific current-data blockers, not proof that future data cannot support a new registration.

No old same-commit case was promoted. This one v2 is a separate, prospective descriptive candidate; public visibility requires its own locked run and evidence review.
