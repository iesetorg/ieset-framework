# Blind registration: SMARD German wind/solar share and wholesale price

**One fixed question:** `smard_german_vre_share_day_ahead_price_2018_2026`.
Only source documentation, schemas, date/region/filter keys, source bytes,
and fetch-manifest metadata were inspected before registration. No selected
`value`, missingness mask, model coefficient, or outcome sign was opened.
The five files have an exact common monthly key roster of 96 dates,
2018-10-01 through 2026-09-01. The committed CSV roster has SHA-256
`5541b2d7ed6c88d5caa2176408340a14445dd747a46ea82be5b1dbbc9343673b`.

The pinned publisher is Bundesnetzagentur/SMARD. The price series represents
the Germany/Luxembourg bidding zone from October 2018 and has units EUR/MWh;
the generation and load files are German monthly MWh. The publisher's
[user guide](https://www.smard.de/resource/blob/205652/63fcff2c9813096fa2229d769da164ef/smard-user-guide-09-2021-data.pdf)
describes these definitions and historical revisions. This geography
mismatch is disclosed and cannot be solved by relabelling the country.

| Role | Pinned local vintage | SHA-256 |
| --- | --- | --- |
| Price | `data/vintages/smard/price_de_lu_DE_month@2026-10-09T121732Z.parquet` | `6f0447b805603f7a2e6ff917bc8e57e80697e05efe9dbe6b035e1e9253a6c14e` |
| Solar | `data/vintages/smard/solar_DE_month@2026-10-09T121736Z.parquet` | `025836509aad657121bbb46286ce60059c3b3b697773239cb86a156f495ea4dd` |
| Onshore wind | `data/vintages/smard/wind_onshore_DE_month@2026-10-09T121740Z.parquet` | `b2d24dfb71569ecd534432cd460a9eefca93a12cb429399fff943581c1524529` |
| Offshore wind | `data/vintages/smard/wind_offshore_DE_month@2026-10-09T121744Z.parquet` | `6931c817a5c55c1bf326e0497ae42622dd02e4f967215f8bf2d0b5bd9f486608` |
| Load | `data/vintages/smard/load_DE_month@2026-10-09T121805Z.parquet` | `a73d3b489ed62e0eceb0e7deef6072b6c46c4d78937ae3e29fec00dcce931d0d` |

All five entries appear once in the local fetch manifest
`data/manifests/fetch_run_2026-10-09T121824Z.yaml` with SHA-256
`befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960`.
The manifest is not copied into the branch because it carries unrelated
local filesystem paths. The exact file bytes are held in the user's local
source checkout and verified through a separately committed relative-path
lock. Publisher HTTP response bytes were not separately preserved.

The YAML fixes the estimator, gates and verdicts. Keep at least 84 complete
months and six full years, a five-point share IQR, and a full-rank model.
Fit OLS with log load, calendar-month and calendar-year indicators; use
three-lag HAC uncertainty. An association needs two-sided p<=0.01, an
absolute slope of at least 1 EUR/MWh per 10 share points, and at least
five of seven fixed year-omission slopes in the same direction. Otherwise
the estimable verdict is PARTIAL; gate failure is INCONCLUSIVE. The local
test is descriptive, with no causal, policy, school, position or featured
credit. One question is counted once.

Commit the YAML, steelman, this plan, key-only roster and guarded runner
together. Commit the source lock in a later commit before values are read.
Run once, retain any failure, and verify exact artifact replay.
