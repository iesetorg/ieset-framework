# Export-market concentration and later export-share volatility — preregistration

This is one fixed **descriptive** forward calibration. The WITS source
field named product_concentration actually contains
HH-MKT-CNCNTRTN-NDX, the **market** Herfindahl-Hirschman concentration
index across export destination partners. WITS distinguishes that
index from product concentration. The archived
wits_export_product_diversification_resilience_panel generic screen was
PARTIAL (beta −1.849, p 0.152 under its own model) and mislabeled this
market series as product concentration. This new ID tests a corrected
market claim and leaves the old verdict, credit, and claim untouched.

## Knowledge and source boundary

Before registration, only source byte hashes, schemas, country/year keys,
WITS indicator/partner/product metadata, fetch manifests, official
definitions, and the archived generic screen were inspected. No selected
WITS or WDI values, missingness flags, coefficients, or model fits were
opened. The key-only roster has 149 ISO 3166 alpha-3 economies/territories
with WITS 2000 and 2010 keys and every WDI annual key from 2000 through
2020. XKX is permitted by the key filter but lacks complete keys here.
The roster at
data/pinned_evidence/wits_market_concentration_export_share_volatility_key_roster.csv
has SHA-256
28254b72c7a9ec09fa6d2b8d12989f4d5d0c4809eecdd7deff3426e6dbe5bd02.
Key presence does not imply a non-null reading.

| Source | Exact vintage SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- |
| WITS product_concentration 2026-07-23T151543Z, actual HH-MKT-CNCNTRTN-NDX | c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949 | 96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5 |
| WDI NE.EXP.GNFS.ZS 2026-05-05T203013Z | a53b48aa292a8b461a32c19943ad7bbca52f3625899a79d7c92e640724cfb121 | 53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0 |

The WITS fetch manifest lists World Bank WITS terms. This design commits
only source metadata and derived summary estimates; no row-level WITS
values. Exact replay requires the hash-pinned raw vintage under its
applicable terms.

## Fixed estimand

For each roster economy, require WITS market HHI in [0,1] for 2000 and
2010 and WDI goods-and-services exports/GDP in [0,300] for **every**
year 2000–2020. No interpolation, imputation, winsorisation,
replacement, or post-result geography selection. The exposure is
(HHI_2010 − HHI_2000) / 0.1. For each year 2001–2010 and 2011–2020,
take the annual percentage-point change in exports/GDP from the
immediately prior year. The outcome is the sample standard deviation
(denominator 9) of the ten 2011–2020 changes; the prior-period control
is the same statistic for the ten 2001–2010 changes.

Fit equal-economy OLS of later volatility on exposure, controlling 2000
market HHI, 2010 export/GDP share, and prior-period volatility, with an
intercept. Use HC3 robust standard errors and a two-sided Student t
reference with N−5 degrees of freedom. This is one fixed model.

## Frozen data, influence, and verdict gates

Require at least 80 complete economies, 20 with absolute HHI change of
at least 0.05, and HHI-change interquartile range at least 0.03.
Require full rank, finite positive HC3 uncertainty, no economy above
20% of squared exposure residual after controls, no economy above 25%
of squared outcome residual after controls, and at most two failed
leave-one-economy-out fits. Any failure is **INCONCLUSIVE**.
Otherwise **SUPPORTED** requires beta at least +1 volatility point per
+0.1 HHI change, two-sided p≤0.01, and positive beta in at least 75%
of successful leave-one-out fits. **REFUTED** requires beta at most −1,
the same p cutoff, and negative beta in at least 75% of successful
leave-one-out fits. Every other estimable result is **PARTIAL**. No
causal, policy, school, position, or featured credit is awarded.

## Measurement limits and chronology

The WITS index is for merchandise export destination markets. WDI
exports include goods and services, and its GDP denominator can move
independently of export values. This outcome cannot attribute volatility
to partner shocks. The 2020 endpoint includes pandemic disruption.
These limitations prevent a causal or policy interpretation.

1. Commit this plan, runner, spec, steelman, and key-only roster
   together, without selected values or a result.
2. Commit a separate metadata-only source lock after source-byte and
   fetch-manifest verification.
3. Only then open selected values, run every frozen gate, and commit
   the result audit and nine run artifacts without hiding failures.
4. Replay against the original raw vintages, comparing all outputs byte
   for byte. Refresh shared indexes after reviewed integration.

Definitions: [WITS Trade Outcomes Help](https://wits.worldbank.org/WITS/WITS/TradeIndicatorsHelp/TradeOutcomes_Help.htm?AspxAutoDetectCookieSupport=1)
and [World Bank exports of goods and services/GDP](https://data.worldbank.org/indicator/NE.EXP.GNFS.ZS).
