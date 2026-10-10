# Education spending and six educational milestones — preregistration

This is one closed, six-test **descriptive** family. The six outcomes mark
different stages or stocks of education: primary completion, secondary net
enrolment, tertiary gross enrolment, adult literacy, adult upper-secondary
attainment, and adult bachelor's attainment. They are correlated measures of
the same broad education system, so six nominal results are not six
independent replications. The family-wide directional cutoff is the two-sided
Bonferroni value 0.01/6, with all six tests retained in the denominator even
if one fails a frozen data gate.

## Knowledge boundary

Older IESET candidate runs of broad education-spending hypotheses are already
visible. In particular, an older alias-repair candidate paired education
spending with tertiary enrolment. This new-ID family uses a new, fixed
three-year forward change and a declared common family rule. It is not a
blind replication of that older result, and it does not regrade the older
school or policy claims. Before this registration, only source names,
vintage identities, hashes, country/year keys, and the official indicator
descriptions were inspected. No selected values, missingness flags, outcome
coefficients, or fits from this family were opened.

## Frozen source and roster

The runner and six specifications pin exact WDI Parquet SHA-256 hashes plus
tracked fetch-manifest hashes for education spending, real GDP per person,
real GDP growth, and all six outcomes. The key-only roster is the intersection
of ISO 3166 alpha-3 economies from `pycountry` plus `XKX` with every required
country/year key for 2000–2021 in those nine files. It has 216 economies and
is frozen at `data/pinned_evidence/wdi_education_spending_milestones_key_roster.csv`
(SHA-256 `a7b8e33e420cd1c0ce8160ad4e03e1102440d184842dd450027a446df26e8638`).
The roster says nothing about non-null values. WDI source URLs and UNESCO UIS
attribution are carried from the fetch manifests. The selected source slices
will be made only after this registration is committed.

## Estimand and method

Each economy contributes year `t` from 2000–2018 if government education
expenditure/GDP, the outcome at `t` and exact `t+3`, real GDP per person at
`t`, and GDP growth at `t` are present and within the fixed ranges. The
outcome is the percentage-point change from `t` to `t+3`. The exposure is
the education-expenditure share at `t`, in percentage points of GDP. Exclude
missing/invalid cells; do not interpolate, replace, winsorise, or select an
outcome-specific country list after measurement. Spending must be in (0,30],
income positive, GDP growth in [-100,100], and both outcome readings in
[0,150] for primary completion, [0,200] for gross tertiary enrolment, or
[0,100] for each other measure.

For each outcome, require at least three complete pairs per economy, 150
pairs overall, 20 economies, and 12 economies with at least a 0.5 percentage
point within-country spending range. Fit equal-pair OLS of the three-year
outcome change on spending, baseline outcome, log real GDP per person, and
GDP growth, with economy and anchor-year fixed effects. Use country-clustered
standard errors and a two-sided Student t reference with `G−1` degrees of
freedom. Partial out the same controls and fixed effects from spending before
checking concentration: no economy may supply over 25% and no anchor year
over 20% of residualized spending variation. Require full-rank design and
finite positive uncertainty.

Any failed data or method floor is `INCONCLUSIVE` with no coefficient offered
for public calibration. Otherwise `SUPPORTED` means beta at least +1.0
outcome point over three years per +1 GDP point of spending and p≤0.01/6;
`REFUTED` means beta at most −1.0 and the same p cutoff; all other estimable
results are `PARTIAL`. No alternative outcome, lag, control set, sample,
significance level, or test denominator is substituted after values are read.

Spending/GDP can move because the GDP denominator changes, governments may
spend in response to low attainment, and the milestones have different
populations and reporting gaps. The fixed effects and ordering do not
identify a policy effect. Every verdict receives zero causal, policy,
school, position, and featured credit. The six-test adjustment is local to
this batch and does not correct earlier IESET archive-wide selection.

## Required chronology

1. Commit this plan, runner, key roster, six specs, and six steelmen together.
   The commit must contain no selected values or result artifacts.
2. Run the frozen runner's `--lock` against the hash-pinned source root. It
   writes only a narrow value slice and custody manifest. Commit those two
   files in a later commit; the source lock must contain no estimates.
3. Run `--run` only after the lock commit. Keep every failure, then commit all
   six run folders and the family result audit in a third commit.
4. Run `--verify-source` against the original vintages and `--verify` against
   the committed results. Refresh the shared indexes only after integration.

Official indicator definitions: [education expenditure](https://data.worldbank.org/indicator/SE.XPD.TOTL.GD.ZS),
[primary completion](https://data.worldbank.org/indicator/SE.PRM.CMPT.ZS),
[secondary net enrolment](https://data.worldbank.org/indicator/SE.SEC.NENR),
[tertiary enrolment](https://data.worldbank.org/indicator/SE.TER.ENRR),
[adult literacy](https://data.worldbank.org/indicator/SE.ADT.LITR.ZS),
[upper-secondary attainment](https://data.worldbank.org/indicator/SE.SEC.CUAT.UP.ZS),
and [bachelor's attainment](https://data.worldbank.org/indicator/SE.TER.CUAT.BA.ZS).
