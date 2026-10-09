# Business R&D and tertiary employment: prospective registration

This is one new measured associational question, not a repair of an old run.
Neither candidate numeric values nor null masks were opened to select the
design. The spec, steelman, runner, verifier, and this plan must share a
first-addition commit. A source lock is committed separately before any
measured column is read; results enter a third commit and remain inspectable
whether supported, refuted, partial, or inconclusive.

In a fixed 35-country panel, higher business-enterprise R&D expenditure as a
share of GDP at calendar year `t` is hypothesized to predict a higher change
in the employment rate of tertiary-educated people aged 25–64 from `t` to
`t+3`. Eurostat treatment `rd_e_gerdtot` selects `freq=A, sectperf=BES,
unit=PC_GDP`; direct outcome `lfsa_ergaedn` selects `freq=A, citizen=TOTAL,
isced11=ED5-8, sex=T, age=Y25-64, unit=PC`. This outcome is an **employment
rate among tertiary-educated people**, not tertiary employment headcount, job
quality, wages, or R&D-sector hiring.

The fixed years are 1995–2021. Exact dimension and country-year keys give a
773-pair/35-country upper envelope after five key years per country; values
and missingness can reduce it. Require at least 400 complete pairs, 25
countries, five complete treatment years per retained country, and 15
within-country exposure-varying countries. Require finite treatment and both
employment-rate endpoints in [0,100], with no imputation or country swap.
Estimate one country/year fixed-effect OLS coefficient controlling for the
baseline tertiary employment rate; use country-clustered normal-Wald
uncertainty. A negative coefficient at two-sided `p<=0.01` refutes the stated
direction; a positive one at that cutoff supports it; every other estimable
result is partial. Failed sample/rank/uncertainty gates are inconclusive.
The 0.01 single-test screen is deliberately conservative after earlier
cross-domain results were visible; it is not a claim of global correction
across every IESET hypothesis.

The treatment source is absent from the registered hypothesis corpus by
exact source-string search. Two older welfare-transfer specs use the labour
source, so the outcome vintage is not globally unseen. This is a distinct
source pair and estimand, not an independent welfare-policy replication.
R&D intensity may follow skilled employment or a common growth shock; sector
mix, education composition, and GDP-denominator changes can move both series.
No causal, policy-effect, position, featured, or school-score credit is
permitted. Both raw Parquet slices lack retained observation/status flags.

| Role | Raw path | SHA-256 | Tracked manifest |
| --- | --- | --- | --- |
| Business R&D intensity | `data/vintages/eurostat/rd_e_gerdtot@2026-05-05T210242Z.parquet` | `fea284d7b17e31a3803749fca052f6a110ed1b8e703a9151964d1d15f58df152` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| Tertiary-educated employment rate | `data/vintages/eurostat/lfsa_ergaedn@2026-04-30T125100Z.parquet` | `6bdae02133c40b7498922a0a1fa2b28d3e63fcde3fff3915353e87275c78edc3` | `data/manifests/fetch_run_2026-04-30T125203Z.yaml` |

Raw vintages are ignored by Git. Exact replay elsewhere requires recovering
these same bytes and verifying the tracked manifest pins.
