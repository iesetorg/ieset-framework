# FAOSTAT relative-price crop supply family — result and custody review

This family adds eight public **descriptive calibration** records, not eight independent replications or policy effects. The complete universe was set as four FAOSTAT food-crop groups (cereals 1717, roots/tubers 1720, pulses 1726, oilcrops 1732) crossed with two distinct supply margins (harvested area 5312 and yield 5412). Each predictor is its group producer-price-index growth relative to the overall Agriculture index 2051; the outcome is next-year growth in the same group's area or yield. Overlapping country-years, group prices and agronomic margins make the tests correlated. The fixed family rule was a two-sided **p ≤ 0.00125** (0.01/8) plus coefficient magnitude at least 0.05 log growth per log relative-price change; all eight cells stayed in the denominator.

## Frozen chronology and source custody

- Integrated baseline merge: `9e045b93b65a2f77723d0a4f34a75829ab497bd7`.
- Blind key-only registration: `aabcd76a57da07d02aeb95fd8c02b5a3dad0ce25`, with all eight claims, exact selectors, fixed model/gates, steelmen, runner, synthetic tests, and a 35,041-row key roster. Only schemas, item/element/year/country keys, codebooks and source hashes had been read; selected numeric values, flags and null masks remained unopened.
- Separate source lock: `5d3acb1db8bf38fc12f2028af00cfe811e00d9dc`, fixing the exact official ZIP archive and derived-Parquet SHA-256 hashes before selected measurement.
- Narrow post-measurement card amendment: `0f44a38630679c6c4e17f04e36f7b64e0ea5631d`, with a contemporaneous note and synthetic tests. It adds prominent E-flag provenance wording to public cards and an amendment chronology guard; source selectors, admitted flags, country/year roster, estimator, exclusions, family threshold, coefficients and verdicts did not change. The result artifacts were still uncommitted when this amendment was made.
- First result commit: `84b5322b554a9e73ddfe02ee8c562f3198b4ef78`.

A separate deterministic audit compared every selected source row in each official ZIP CSV with its local derived Parquet row, including rows later excluded by geography, flag or model gates. **24,766 price rows and 104,465 crop rows matched exactly** by key, binary64 numeric value, flag and unit; the comparison and digests are in `engine/audits/faostat_archive_parquet_selection_check_2026-10-10.json`. This establishes selected archive-to-Parquet parity for the pinned files. The raw archives remain in the ignored local cache and are **not in Git**, so exact replay requires those SHA-matching files; there is no tracked original fetch manifest or proof of FAO's upstream country collection process.

## All eight frozen results

| Crop group | Later margin | Beta | Two-sided p | Country-years | Countries | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Cereals | Harvested area | +0.04181 | 0.010430 | 4,233 | 151 | PARTIAL: p and magnitude gates fail |
| Cereals | Yield | +0.05937 | 0.003421 | 4,168 | 152 | PARTIAL: family p gate fails |
| Roots/tubers | Harvested area | +0.04668 | 0.000021 | 4,238 | 161 | PARTIAL: magnitude gate fails |
| Roots/tubers | Yield | +0.03990 | 0.000417 | 4,319 | 160 | PARTIAL: magnitude gate fails |
| Pulses | Harvested area | **+0.07796** | **0.000207** | **3,757** | **141** | **SUPPORTED** |
| Pulses | Yield | −0.00102 | 0.955314 | 3,759 | 141 | PARTIAL |
| Oilcrops | Harvested area | **+0.08717** | **0.0000387** | **3,929** | **150** | **SUPPORTED** |
| Oilcrops | Yield | +0.02464 | 0.201667 | 3,909 | 151 | PARTIAL |

Every cell cleared the precommitted measured-sample floor (500 rows/30 countries), material-exposure floor (100 rows/20 countries), country-year minimum, full-rank, finite country-cluster uncertainty and ≤20% top-country residualized-exposure share gates. The two supported area cells have 2,299 material exposure rows in 141 countries (pulses) and 2,390 in 149 countries (oilcrops); their top-country residualized-exposure shares are 0.02389 and 0.02075. Coefficients imply approximately 0.78% and 0.87% greater next-year area log growth for a 10% relative-price log increase within the measured panels, respectively, before causal interpretation. Exact coefficients, standard errors and family-adjusted confidence intervals are in each diagnostic packet.

## Material flag and interpretation limits

**Every complete-case producer-price index input used by both supported cells is FAOSTAT `E` (estimated)** at t−1 and t, both for the crop-group index and overall Agriculture index. For the pulses area cell, all four price-index roles were E-coded in each of 3,761 complete rows before the country floor. Its later-area outcome at t+1 was 2,534 `A` official, 1,187 `E` estimated and 40 `X` external-organization rows. The earlier pulses-area outcome flags were t−1: 2,565 A / 1,152 E / 44 X; t: 2,551 A / 1,167 E / 43 X. Four rows then failed the minimum-years-per-country rule, leaving 3,757 model rows.

For the oilcrops area cell, all four price-index roles **and all three crop-outcome years** were E-coded in each of 3,931 complete rows before the country floor; two rows failed the minimum-years-per-country rule, leaving 3,929 model rows. Thus its `SUPPORTED` label means support for a descriptive association in **entirely estimated aggregate series**. Neither supported label is evidence of an independently observed farmer response. The card amendment makes these E-flag limits visible beside each verdict.

Crop-group price indices and group-level yields can reflect commodity composition; harvested area can count multiple harvests of a parcel. Same-year harvest shocks can raise price, and weather, input costs, trade, currency and subsidies can move both price and future production. Country/year effects and prior outcome growth do not identify a causal response. These records receive **zero causal, policy, school, position and featured credit**. The within-family Bonferroni rule does not correct archive-wide family selection.

## Verification and public tier

- Final runner exact-replayed all eight packet directories after the flag amendment; archive/Parquet comparison exact-replayed separately.
- `scripts/validate_specs.py` passed all 6,415 repository specification files, with 28 existing permitted candidate-policy forward-reference warnings. Synthetic original and amendment guard tests passed. `scripts/check_public_opsec.py` passed.
- `scripts/check_preregistration.py` reported 913 strict preregistration pairs; all eight new IDs are `verified`. The read-only evidence-tier calculation classified all eight as `calibration`, public-visible, with no exclusion reasons. Public-visible total in this isolated checkout is **640**, eight above the integrated 632 baseline. Generated site/index outputs were not committed.

Official source documentation: [FAO agricultural producer prices](https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1), [FAO crop area/yield/production](https://data.fao.org/catalog/iso/d24a448b-3b62-4c09-8c1d-4a39bb599876), and [FAO statistical database terms](https://www.fao.org/contact-us/terms/db-terms-of-use/en). FAO did not sponsor or endorse this interpretation.
