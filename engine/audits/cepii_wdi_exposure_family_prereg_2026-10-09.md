# CEPII Gravity × WDI exposure family preregistration — 2026-10-09

This is one prospective **three-test descriptive family**, registered before
reading its treatment or outcome values. The source-only preflight read
`country_iso3` and `year` columns and source SHA-256 bytes. The three measured
columns are independent of `rta_coverage`; the version-specific RTA label
discrepancy is recorded separately in
`engine/audits/cepii_rta_coverage_label_crosscheck_2026-10-09.md`.

The prior `liberal_free_trade_partner_growth_panel_1990_2020` same-commit
candidate used a CEPII FTA-accession indicator and WDI trade openness/GDP.
Its visible PARTIAL result failed the estimator floor after a rank-deficient
staggered-DiD fallback. All **61** countries named in that old specification
are excluded here, including countries that may not have fitted old rows:

`ARG AUS AUT BEL BGD BRA CAN CHE CHL CHN COL CRI CZE DEU DNK DOM ECU EGY ESP EST FIN FRA GBR GRC GTM HND HUN IDN IND IRL ISR ITA JOR JPN KOR LTU LVA MAR MEX MYS NIC NLD NOR NZL PAK PAN PER PHL POL PRT ROU SGP SLV SVK SVN SWE THA TUR USA VNM ZAF`

Other IESET treaty-event calibrations measure directed, nominal CEPII BACI
goods flows around individual accessions, often with failed pretrend gates.
The cases below instead test country-year macro associations. They are **not**
new evidence for those event effects or independent replications of one
another. B and C share FTA exposure and the same CEPII archive; all three
share the WDI family and many possible countries.

| ID suffix | Fixed exposure at year t | Exact outcome change t→t+1 | Treatment years | Key-only upper envelope after old-country exclusion |
| --- | --- | --- | --- | ---: |
| `foreign_market_potential_trade_open_change` | log change from t−1 to t in CEPII partner GDP divided by distance | WDI trade in goods and services as % GDP | 1961–2020 | 8,300 pairs / 151 countries |
| `fta_market_potential_private_investment_change` | FTA-covered share of distance-weighted partner GDP | WDI private gross fixed capital formation as % GDP | 1990–2020 | 4,556 / 151 |
| `fta_partner_gdp_hightech_export_change` | FTA-covered share of observed partner GDP | WDI high-tech exports as % manufactured exports | 1995–2020 | 3,861 / 151 |

The key counts are **upper bounds**, because WDI files retain rows with null
values. No value, missingness mask, exposure variation, coefficient, or
outcome sign was screened to choose these cases or floors.

Each case uses exact t−1, t and t+1 calendar-year joins, no interpolation,
country and treatment-year fixed effects, baseline outcome at t and log real
GDP per person at t as controls, with country-clustered standard errors. The
primary outcome is the level at t+1 minus the level at t. Each requires at
least five complete pairs per country. Case A requires at least 800 complete
pairs, 50 countries and 35 countries with nontrivial within-country exposure
variation. B and C each require 400 complete pairs, 35 countries, 25
within-country exposure-varying countries (range ≥0.01 share unit), and 200
positive-share rows. Singular or nonfinite fits are INCONCLUSIVE. No
covariate, country, window or threshold may be replaced after looking at
values.

All three expected signs are positive. A two-sided country-clustered
coefficient p≤0.05/3 (1/60) in the expected direction is SUPPORTED; the same
threshold in the opposite direction is REFUTED; any other estimable result is
PARTIAL. A failed data/variation/estimator gate is INCONCLUSIVE. The fixed
family includes all three tests whatever their results. Every result is
calibration-only, with zero causal, policy, featured, position, or school-score
credit.

The first-addition registration commit must contain these three specs,
steelmen, this plan, and the guarded runner. A separate later commit locks
the seven exact local source files and CEPII raw ZIP by SHA-256. Only after
both commits may the runner load measured columns; results are committed
separately and independently replayed. The CEPII Gravity V202211 archive is
under [Etalab Open Licence 2.0](https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=8)
and must be attributed to Conte, Cotterlaz and Mayer (2022). WDI series are
World Bank [CC BY 4.0](https://data.worldbank.org/indicator/NE.TRD.GNFS.ZS).

Measurement limits: partner GDP in CEPII is current-dollar and coverage can
shift; geography is not an instrument; trade and investment ratios share GDP
denominators with economic cycles; FTA agreement status is neither tariff
intensity nor implementation depth; high-tech manufactured-export share is
not exporter-product concentration. Country/year controls and next-year
ordering do not identify an effect.
