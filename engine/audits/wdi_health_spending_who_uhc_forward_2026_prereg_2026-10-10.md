# Earlier health spending and later WHO UHC service coverage — preregistration

This is one fixed **descriptive** forward calibration. The predictor is the
2000–2010 change in **total current health expenditure/GDP**, not public
health spending. The endpoint is 2010–2020 change in the WHO UHC *service
coverage index*, not mortality, care quality, or financial protection.
The prior generic public_health_spending_avoidable_mortality_panel run is
already known as REFUTED under its legacy method. It is a distinct
claim/outcome, receives no changed verdict or credit here, and means this
is not a blind archive-wide discovery exercise.

## Knowledge and source boundary

Before this registration, only source byte hashes, schemas, country/year
keys, WHO SpatialDimType, manifest metadata, and official indicator
definitions were inspected. No selected values, null masks, observation
status, coefficients, model fits, or post hoc geography partitions were
opened. The key-only candidate roster contains 193 ISO 3166 alpha-3
economies/territories with all required keys; the eligibility rule also
permits XKX, which lacks the complete key set here. The roster is stored in
data/pinned_evidence/wdi_health_spending_who_uhc_key_roster.csv, SHA-256
34702ce92aa78d7e24b63744e33cfc2d09a0537333fcad2c08f5bc1404067270.
A present source key does not guarantee a measured value.

| Source | Frozen vintage SHA-256 | Fetch manifest SHA-256 | Keys |
| --- | --- | --- | --- |
| WDI SH.XPD.CHEX.GD.ZS 2026-05-05T203513Z | ca58050bf93fd11b1b864f04c8d27eaedbd6e260eba3a7e5df473a8cb0b5cc40 | 5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112 | 2000, 2010 |
| WHO UHC_INDEX_REPORTED 2026-04-30T114740Z | e4e1fea6a88f1cfcb97599a762f3c3988d5e2bff3674458f94f13e9710c35b1a | e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e | 2000, 2010, 2020 COUNTRY |

The runner checks the full source-file hashes and exact tracked fetch
manifest entries. WHO's fetch manifest labels its source
**CC-BY-NC-SA-3.0 IGO**. This design records metadata, derived summary
statistics, and a result; it does not copy row-level WHO values into tracked
artifacts. Exact replay requires licensed access to the pinned raw vintage.

## Fixed estimand and gates

For each roster economy, retain only finite WDI expenditure shares in
(0,100] at both years and finite WHO index readings in [0,100] at all
three years. Do not interpolate, impute, winsorise, replace, or alter the
country set after values are read. Fit equal-economy OLS of
UHC_2020 − UHC_2010 on CHE_2010 − CHE_2000, controlling
UHC_2010, UHC_2010 − UHC_2000, and CHE_2000, with an intercept.
Use HC3 standard errors and a two-sided Student t reference with N−5
degrees of freedom. There is one test and no model search.

The frozen data floors are 80 complete economies, 20 with absolute
expenditure-share change of at least 0.5 GDP percentage point, and a
change interquartile range of at least 0.5 point. Require full rank,
finite positive HC3 uncertainty, no economy over 20% of residualized
exposure squared variation, and at most two failed leave-one-economy-out
fits. Any failure is **INCONCLUSIVE**. Otherwise **SUPPORTED** requires
beta at least +1 WHO index point per +1 GDP point of spending-share
change, two-sided p≤0.01, and positive beta in at least 75% of successful
leave-one-out fits. **REFUTED** requires beta at most −1, the same p
cutoff, and negative beta in at least 75% of successful leave-one-out
fits. All other estimable results are **PARTIAL**. No causal, policy,
school, position, or featured credit is awarded.

## Required chronology

1. Commit this plan, runner, spec, steelman, and key-only roster together.
   The commit must have no selected values, source lock, or run result.
2. Produce the metadata-only lock from the hash-pinned raw vintages and
   commit it separately. The lock records no selected values or fit.
3. Only after that lock commit, run the fixed model, preserve all failures,
   and commit the result audit and nine standard run artifacts.
4. Replay from the original raw vintages and compare every artifact byte
   for byte. Refresh shared indexes only after reviewed integration.

Official definitions: [World Bank current health expenditure](https://data.worldbank.org/indicator/SH.XPD.CHEX.GD.ZS)
and [WHO UHC service coverage index](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/uhc-index-of-service-coverage).
