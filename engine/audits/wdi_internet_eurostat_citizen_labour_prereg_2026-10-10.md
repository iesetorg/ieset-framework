# Preregistration: WDI Internet uptake × Eurostat citizenship labour rates

Family `wdi_internet_eurostat_citizen_labour_2026_10_10`; 64 precommitted cells: 2 distinct outcomes (activity and employment) × 2 citizenship classes (national/foreign) × 2 sexes × 8 nonoverlapping five-year ages 20–59. All 64 share one Bonferroni family alpha 0.01 (individual two-sided cutoff 0.00015625). The two outcome measures and demographic cells are correlated; do not call them independent replications.

Frozen runner: `scripts/run_wdi_internet_eurostat_citizen_labour_2026.py`. Frozen case/country/year key roster: `data/pinned_evidence/wdi_internet_eurostat_citizen_labour_2026_key_roster.csv` SHA-256 `ed255398f42704075825c4e76db3dab2003ef2cfe6c12a8c24086c380b368758`. All 64 specifications and the family steelman are committed together as the registration commit. A separate source-lock commit is required before either Eurostat selected value or null mask can be read.

## Source custody and meanings

- internet: `data/vintages/world_bank_wdi/IT.NET.USER.ZS@2026-05-05T203400Z.parquet` SHA-256 `c17944e3e8ef15a5c5663e281389ad5bcc1398ae3769258c75f545f37b216cb8`; manifest `data/manifests/fetch_run_2026-05-05T210519Z.yaml` SHA-256 `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112`.
- activity: `data/vintages/eurostat/lfsa_argan@2026-04-30T130700Z.parquet` SHA-256 `0ed2c40356794d48779dff7fc951e022cfb7994b1d7be5249f16fed12627dec9`; manifest `data/manifests/fetch_run_2026-04-30T130723Z.yaml` SHA-256 `cdb19507131f6659ca87ec4aa96784f031627a8bab939dc9ec9390752778aa16`.
- employment: `data/vintages/eurostat/lfsa_ergan@2026-04-30T130634Z.parquet` SHA-256 `e0129dac7799748fad79571d6b736cf9afb55d290fe4c6b8f95457af8e1eee68`; manifest `data/manifests/fetch_run_2026-04-30T130700Z.yaml` SHA-256 `63fb4149706f480f087beeab88cfd049b870d26ca689edbdd2f227c039a158dd`.

Eurostat source definitions: https://ec.europa.eu/eurostat/cache/metadata/en/lfsa_esms.htm ; WDI Internet-use definition and underlying ITU source: https://databank.worldbank.org/metadataglossary/world-development-indicators/series/IT.NET.USER.ZS . Treat publisher licence labels as insufficient for public rights clearance.

## Key-only feasibility, before outcome values

Only Eurostat dimensions and country/year keys were read. No selected Eurostat value, null mask, sign, fit, or observation flag was read. WDI Internet-use values/statuses alone were inspected to fix the lagged exposure, cap, and material change. The 2005–2018 anchor window ends at 2019 outcomes, before the known 2021 LFS redesign. The source Parquet does not retain Eurostat quality flags.

| Cell | Key pairs | Countries | Material ≥2pp pairs | Material countries |
| --- | ---: | ---: | ---: | ---: |
| `activity_nat_f_20_24` | 418 | 30 | 267 | 30 |
| `activity_nat_f_25_29` | 418 | 30 | 267 | 30 |
| `activity_nat_f_30_34` | 418 | 30 | 267 | 30 |
| `activity_nat_f_35_39` | 418 | 30 | 267 | 30 |
| `activity_nat_f_40_44` | 418 | 30 | 267 | 30 |
| `activity_nat_f_45_49` | 418 | 30 | 267 | 30 |
| `activity_nat_f_50_54` | 418 | 30 | 267 | 30 |
| `activity_nat_f_55_59` | 418 | 30 | 267 | 30 |
| `activity_nat_m_20_24` | 418 | 30 | 267 | 30 |
| `activity_nat_m_25_29` | 418 | 30 | 267 | 30 |
| `activity_nat_m_30_34` | 418 | 30 | 267 | 30 |
| `activity_nat_m_35_39` | 418 | 30 | 267 | 30 |
| `activity_nat_m_40_44` | 418 | 30 | 267 | 30 |
| `activity_nat_m_45_49` | 418 | 30 | 267 | 30 |
| `activity_nat_m_50_54` | 418 | 30 | 267 | 30 |
| `activity_nat_m_55_59` | 418 | 30 | 267 | 30 |
| `activity_for_f_20_24` | 269 | 21 | 157 | 21 |
| `activity_for_f_25_29` | 300 | 23 | 174 | 23 |
| `activity_for_f_30_34` | 301 | 23 | 174 | 23 |
| `activity_for_f_35_39` | 303 | 23 | 176 | 23 |
| `activity_for_f_40_44` | 305 | 23 | 177 | 23 |
| `activity_for_f_45_49` | 305 | 23 | 178 | 23 |
| `activity_for_f_50_54` | 288 | 22 | 168 | 22 |
| `activity_for_f_55_59` | 267 | 21 | 156 | 21 |
| `activity_for_m_20_24` | 291 | 22 | 170 | 22 |
| `activity_for_m_25_29` | 306 | 23 | 180 | 23 |
| `activity_for_m_30_34` | 322 | 25 | 191 | 25 |
| `activity_for_m_35_39` | 324 | 24 | 195 | 24 |
| `activity_for_m_40_44` | 309 | 23 | 181 | 23 |
| `activity_for_m_45_49` | 307 | 23 | 180 | 23 |
| `activity_for_m_50_54` | 299 | 23 | 173 | 23 |
| `activity_for_m_55_59` | 275 | 21 | 159 | 21 |
| `employment_nat_f_20_24` | 418 | 30 | 267 | 30 |
| `employment_nat_f_25_29` | 418 | 30 | 267 | 30 |
| `employment_nat_f_30_34` | 418 | 30 | 267 | 30 |
| `employment_nat_f_35_39` | 418 | 30 | 267 | 30 |
| `employment_nat_f_40_44` | 418 | 30 | 267 | 30 |
| `employment_nat_f_45_49` | 418 | 30 | 267 | 30 |
| `employment_nat_f_50_54` | 418 | 30 | 267 | 30 |
| `employment_nat_f_55_59` | 418 | 30 | 267 | 30 |
| `employment_nat_m_20_24` | 418 | 30 | 267 | 30 |
| `employment_nat_m_25_29` | 418 | 30 | 267 | 30 |
| `employment_nat_m_30_34` | 418 | 30 | 267 | 30 |
| `employment_nat_m_35_39` | 418 | 30 | 267 | 30 |
| `employment_nat_m_40_44` | 418 | 30 | 267 | 30 |
| `employment_nat_m_45_49` | 418 | 30 | 267 | 30 |
| `employment_nat_m_50_54` | 418 | 30 | 267 | 30 |
| `employment_nat_m_55_59` | 418 | 30 | 267 | 30 |
| `employment_for_f_20_24` | 245 | 18 | 145 | 18 |
| `employment_for_f_25_29` | 299 | 23 | 173 | 23 |
| `employment_for_f_30_34` | 296 | 22 | 171 | 22 |
| `employment_for_f_35_39` | 301 | 23 | 174 | 23 |
| `employment_for_f_40_44` | 304 | 23 | 176 | 23 |
| `employment_for_f_45_49` | 301 | 23 | 175 | 23 |
| `employment_for_f_50_54` | 283 | 22 | 164 | 22 |
| `employment_for_f_55_59` | 264 | 21 | 155 | 21 |
| `employment_for_m_20_24` | 268 | 21 | 158 | 21 |
| `employment_for_m_25_29` | 304 | 23 | 178 | 23 |
| `employment_for_m_30_34` | 321 | 25 | 190 | 25 |
| `employment_for_m_35_39` | 320 | 24 | 191 | 24 |
| `employment_for_m_40_44` | 309 | 23 | 181 | 23 |
| `employment_for_m_45_49` | 304 | 23 | 178 | 23 |
| `employment_for_m_50_54` | 286 | 22 | 164 | 22 |
| `employment_for_m_55_59` | 274 | 21 | 159 | 21 |

## Frozen estimator and outcomes

For each case and anchor year t, x is national Internet-use percentage at t−1 minus t−2, bounded to absolute change ≤20pp; y is exact Eurostat activity or employment rate at t+1 minus t in percentage points. Regress y on x, Internet level at t−2, country fixed effects, and year fixed effects. Equal country-year weight. CR1 country clusters and Student t(G−1). No secondary fit can upgrade. Require exact source hashes, roster, chronology, finite rate endpoints in [0,100], at least five complete years/country, case-specific minimum pairs/countries/material pairs, ≥12 distinct years, full-rank design, finite positive cluster SE, residualized-x top 1% squared share ≤0.30, any-country share ≤0.20, any-year share ≤0.20. National-citizen cells require 350 pairs/26 countries and material 200 pairs/25 countries; foreign-citizen cells require 200/16 and material 100/15.

SUPPORTED requires beta≥+0.02 rate percentage point per 1pp Internet-use gain and two-sided p≤0.00015625. REFUTED requires beta≤−0.02 at the same p. Estimable failures are PARTIAL; gate failures are INCONCLUSIVE and stay archived. No causal, policy, school, position, or featured credit. The family correction does not cover prior archive-wide hypothesis selection.

## Disclosure

Existing IESET ILO Internet/labour tests and OECD GDP/age-sex employment tests are related. This family adds Eurostat citizenship-specific activity and employment margins; it is not a replication of those questions. National Internet adoption can proxy development; migration and citizenship composition change; LFS sampling error, lost flags and historical breaks limit inference. Public release remains subject to underlying ITU/Eurostat data rights review.
