# WDI prior growth → Eurostat foreign-citizenship immigration: frozen prospective registration

This is a 30-cell descriptive family registered before reading selected Eurostat outcome values or null masks. Preflight inspected only categorical Eurostat keys and WDI treatment values. The preserved datasets predate this registration; prospective refers only to this frozen analysis protocol. Zero policy, causal, school, position or featured credit.

## Source custody and definitions

- WDI `NY.GDP.PCAP.KD` raw `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet`, SHA-256 `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f`; tracked fetch manifest `data/manifests/fetch_run_2026-05-05T200056Z.yaml`, SHA-256 `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945`; official <https://databank.worldbank.org/metadataglossary/sustainable-development-goals-(sdgs)/series/NY.GDP.PCAP.KD>; CC BY 4.0. GDP per capita is in constant 2015 US dollars.
- Eurostat `migr_imm1ctz` raw `data/vintages/eurostat/migr_imm1ctz@2026-05-05T205902Z.parquet`, SHA-256 `b0b178278dd7d1ef68d4a03188e496b580d3e30b61f9fa21c7db13ed547bfeb1`; tracked fetch manifest `data/manifests/fetch_run_2026-05-05T210519Z.yaml`, SHA-256 `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112`; official <https://ec.europa.eu/eurostat/databrowser/view/migr_imm1ctz>, <https://ec.europa.eu/eurostat/web/migration-asylum/international-migration-citizenship/methodology>, <https://ec.europa.eu/eurostat/cache/metadata/en/migr_immi_esms.htm>; dataset manifest `cc_by_4_0`, Eurostat reuse notice <https://ec.europa.eu/eurostat/help/copyright-notice>. Immigration requires establishing usual residence for at least 12 months, having previously resided abroad. `citizen` is legal citizenship, **not** prior residence, birthplace or departure country.

## Frozen dimensions and sample

Fixed citizenship list: AL, AR, BD, BR, CN, CO, DE, DZ, ES, FR, UK, GH, IN, IT, MA, MD, MX, NG, NL, PK, PH, PL, PT, RO, RU, TR, UA, US, VE, VN. Retain annual `freq=A`, count `unit=NR`, total sex `sex=T`, total age `age=TOTAL`, age definition `agedef=COMPLET`, years 2017 and 2019. Exclude national citizenship (`citizen=geo_code`); `UK` maps to GBR for destination WDI; Eurostat EL maps to GRC. Retain sovereign two-letter destinations with WDI positive finite 2013 and 2016 treatment and both Eurostat year keys. No outcome-value completeness screening in the roster `data/pinned_evidence/wdi_eurostat_citizenship_migration_2026_key_roster.csv`, SHA-256 `ae7e1a1cf15e1521f2c6557db743183fec73a032160db2e00cba2b388e33178b`. WDI exposure `X=100*log(GDPpc_2016/GDPpc_2013)`. Do not use source alternatives or other windows.

| Citizenship | Paired destination keys | WDI exposure p90−p10 log pp | Max centered X share |
| --- | ---: | ---: | ---: |
| `AL` | 24 | 8.92 | 0.098 |
| `AR` | 25 | 8.88 | 0.099 |
| `BD` | 25 | 8.88 | 0.099 |
| `BR` | 25 | 8.88 | 0.099 |
| `CN` | 26 | 8.83 | 0.096 |
| `CO` | 25 | 8.88 | 0.099 |
| `DE` | 25 | 9.17 | 0.092 |
| `DZ` | 25 | 8.88 | 0.099 |
| `ES` | 25 | 9.17 | 0.092 |
| `FR` | 25 | 8.88 | 0.099 |
| `UK` | 26 | 9.14 | 0.088 |
| `GH` | 25 | 8.88 | 0.099 |
| `IN` | 26 | 8.83 | 0.096 |
| `IT` | 26 | 9.14 | 0.094 |
| `MA` | 25 | 8.88 | 0.099 |
| `MD` | 24 | 8.89 | 0.101 |
| `MX` | 25 | 8.88 | 0.099 |
| `NG` | 25 | 8.88 | 0.099 |
| `NL` | 25 | 9.17 | 0.089 |
| `PK` | 26 | 8.83 | 0.096 |
| `PH` | 25 | 8.88 | 0.099 |
| `PL` | 26 | 9.14 | 0.088 |
| `PT` | 26 | 9.14 | 0.088 |
| `RO` | 27 | 9.12 | 0.089 |
| `RU` | 25 | 8.88 | 0.099 |
| `TR` | 24 | 8.92 | 0.098 |
| `UA` | 25 | 8.88 | 0.099 |
| `US` | 25 | 8.88 | 0.099 |
| `VE` | 25 | 8.88 | 0.099 |
| `VN` | 24 | 8.92 | 0.098 |

## Frozen outcome, estimator and verdict

For each foreign citizenship, `Y=100*[log1p(immigrant_count_2019)-log1p(immigrant_count_2017)]` in a destination. A complete pair requires two finite **nonnegative** numeric counts; zero is retained via log1p. Report zero, sub-50 and sub-100 endpoint flows and missing/invalid pairs. No imputation, winsorisation, alternate source or post-value sample choice. The raw parquet retains no Eurostat quality flags, so no flag-based filter or quality claim is possible.

Fit one equal-destination cross-sectional OLS with intercept and HC3 standard error. Two-sided Student t uses n−2 degrees of freedom. Require ≥20 complete destinations and ≥15 destinations with counts ≥50 in **both** years, exposure p90−p10 ≥3.0 log percentage points, maximum centered exposure squared share ≤0.35, full rank and finite positive HC3 uncertainty. A failed gate makes the cell INCONCLUSIVE and still counts in the family denominator. The material-flow gate is frozen before counts are opened and does not drop small/zero observations from estimation.

One 30-test Bonferroni correction uses family alpha 0.01, two-sided p≤0.000333333333333 in every cell, including inconclusive cells. SUPPORTED requires beta≥+0.5 outcome log pp per one prior GDP log pp and corrected p; REFUTED requires beta≤−0.5 and corrected p; every other estimable result is PARTIAL. Do not reinterpret a null or gate failure as support. The local correction does not cover wider archive exploration.

## Interpretation and distinctness

The 30 nationality cells are disjoint foreign-citizenship counts, not algebraic copies of the same total. They share country-level growth exposure and period, so they are correlated. This differs from the existing employment/activity-by-age/sex/citizenship LFS family and the weather-to-producer-price family. No citizenship group is treated as an origin-country departure flow. Destination policy, register design, origin crises, networks and common shocks can drive counts; prior GDP growth is an observational proxy for destination opportunity, not a policy intervention. All verdicts remain descriptive calibration only.
