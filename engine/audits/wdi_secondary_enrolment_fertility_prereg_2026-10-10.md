# Prospective one-test registration: secondary enrolment and fertility

**Family ID:** `wdi_secondary_enrolment_fertility_2026_10_10`
**Case:** `wdi_secondary_enrolment_fertility_decade_followthrough_2026`
**Registration boundary:** Only gross secondary-enrolment and real-income
values, source hashes/manifests, and fertility country-year **keys** were
examined. No selected fertility value, null mask, status, coefficient,
model, or sign has been opened. The registration files must share their
first-addition commit. A narrow source lock must be committed separately
and later, before `--run` can read fertility values.

## Direct question and source meaning

Does a larger five-year rise in national gross secondary-school enrolment
from `t−5` to `t` predict a larger proportional fall in national total
fertility from `t` to `t+10`, for three disjoint outcome decades anchored
at `t=1990, 2000, 2010`? Gross enrolment includes both sexes and pupils
outside the official age range, so it can exceed 100%. It is not female
completion, learning, or an education-policy treatment. Total fertility
is births per woman. The outcome is `log(F(t+10)/F(t))`, with negative
values denoting decline. [WDI gross secondary enrolment](https://data.worldbank.org/indicator/SE.SEC.ENRR),
[WDI total fertility](https://data.worldbank.org/indicator/SP.DYN.TFRT.IN).

## Exact pinned custody

| Role | Relative vintage | SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- | --- |
| Schooling | `data/vintages/world_bank_wdi/SE.SEC.ENRR@2026-05-05T204008Z.parquet` | `787f29eb93204dbf11dd408449910c28b523376c054734f1fc68d4215b7b2044` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` `5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112` |
| Fertility | `data/vintages/world_bank_wdi/SP.DYN.TFRT.IN@2026-04-30T130516Z.parquet` | `ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1` | `data/manifests/fetch_run_2026-04-30T130536Z.yaml` `ab56887949d3a51f3e3001ac1065c62538af1db4d4a722e39e29a774447f511b` |
| Baseline real income | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |

The runner verifies full raw and manifest hashes, exact publisher/series/path/
entry hash, immutable registration bytes, separate descendant lock commit,
and no results in either preregistration or source-lock commit. The raw
files are tracked in this checkout. No local machine path appears in the
registered files.

## Frozen key-only eligibility and sample

The three WDI files expose a full country-year grid, so key joins alone
**cannot show outcome completeness**. The 168 registered rows in 72 ISO3
countries are an upper bound. These rows use only schooling and baseline
real-income values plus fertility *keys*. The roster is
`data/pinned_evidence/wdi_secondary_enrolment_fertility_2026_key_roster.csv`,
SHA-256 `ceefc2f69f90551e07fa336260778c11f75ff2a6e7bb1a46725fba8529b45e2c`.
Of the 168 rows, 85 have an absolute schooling change of at least five
percentage points in 57 countries (74 positive and 11 negative material
changes). The finite treatment-only residual variation was broad before
outcome access: the largest 1% of rows account for about 9.2%, and the
largest country about 7.1%, after country and anchor effects plus baseline
real income. The actual gate is recomputed on the complete measured sample
with baseline fertility also residualized.

- Use national ISO3 country codes only and exact anchor years 1990, 2000,
  2010. Require exact schooling values at `t−5` and `t`, GDP per person at
  `t`, and fertility keys at `t` and `t+10`. No neighboring-year match.
- Before outcome access, require finite schooling endpoints in `[0,150]`
  percent, `|schooling(t)−schooling(t−5)|≤40` points, finite positive real
  GDP per person, and at least two candidate windows per country.
- After the separate source lock, require both fertility endpoints finite
  and in `[0.5,10]` births per woman. Drop any invalid pair and then
  countries with fewer than two complete windows. Do not trim on the
  observed fertility change or select countries by the coefficient.
- WDI observation-status fields in these pinned files do not provide
  usable country-specific break flags. No cell is called break-screened,
  and no visual or external break exclusion is allowed after access.

## Frozen model, floors, and verdicts

Primary OLS regresses `log(F(t+10)/F(t))` on the schooling change,
`log(F(t))`, `log(real GDP per person(t))`, country fixed effects, and
anchor-year fixed effects. Cluster by country with CR1 correction;
calculate two-sided Student `t` inference using `G−1` country degrees
of freedom and a 99% interval. The three fertility windows do not
overlap. Require full design rank, at least **140 complete pairs in 60
countries**, at least **65 material changes in 45 countries**, at least
two complete windows per retained country, and finite positive cluster
uncertainty. Residualized schooling variation on the fitted sample may
place at most **30%** of squared residual exposure in the largest 1% of
rows and at most **20%** in any country.

The one-test family fixes two-sided **p≤0.01**. `SUPPORTED` requires beta
at most **−0.003** ten-year log fertility point per +1 schooling-enrolment
point. `REFUTED` requires beta at least **+0.003** with the same p cutoff.
An estimable weaker result is `PARTIAL`; any source, chronology, sample,
exposure, rank, or uncertainty failure is `INCONCLUSIVE`. The one-test
family denominator cannot shrink or be expanded after fertility access.

## Integrity and interpretation

Existing IESET cases address fertility, schooling, labour, family benefits,
and development transitions. An authored-spec scan found no exact WDI
five-year gross-secondary-enrolment change to next-decade WDI total-fertility
change test, but this candidate was still selected from a large archive.
The local p threshold does not correct archive-wide selection. Economic
development, urbanization, contraception, migration, family policies,
conflict, and child mortality can confound the relation. The 2010–2020
window also contains the COVID-19 period. No coefficient supports an
education-policy effect or an individual female schooling mechanism.
Every verdict earns **zero causal, policy, school-score, position, and
featured credit**.

## Required chronology

1. Commit this audit, the YAML spec, steelman, key-only roster, and guarded
   runner together, with no measured result.
2. Run `--write-source-lock` and commit the resulting narrow JSON in a
   separate descendant commit, again with no measured result.
3. Invoke `--run` once and commit the result even if `INCONCLUSIVE`; then
   invoke `--verify` for exact replay before any public index regeneration.
