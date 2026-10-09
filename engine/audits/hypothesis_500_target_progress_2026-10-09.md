# Hypothesis conversion target status — 2026-10-09

The user's latest target was **500 additional public hypothesis records**.
The public evidence ledger had 372 at that point, making the target 872.
After the bounded repair and prospective batches in this sprint, the audited
ledger has **444 public records** (51 featured, 393 calibration) among 1,979
hypotheses. That is **72 additional** relative to the 372 starting point and
**428 short** of the requested increment. No result was made featured by
loosening its gate.

An earlier four-case new-ID batch illustrates the decision boundary:

| New test | Frozen result | Public disposition |
| --- | --- | --- |
| Canada 2024–25 GDP per capita peer holdout | INCONCLUSIVE; all seven required 2025 cells are null in the pinned vintage | Archive; no supportive credit |
| Fed 2025 overnight reverse-repo durability | SUPPORTED under four fixed quarter medians | Descriptive calibration only; missing fetch-time receipt explicitly accepted for that ceiling |
| OECD working-hours/employment country holdout | PARTIAL; 90% interval crosses the equivalence boundary | Associational calibration; no neutrality or policy-effect credit |
| Eurozone 2008/2014 direct distribution measures | PARTIAL; income-share gap clears, relative-poverty gap misses | Descriptive calibration of pinned published observations; quality flags unknown |

All four designs were committed before their value runs, use exact source pins,
and have read-only replay checks. The subsequent Germany 2024–25
manufacturing/electricity comparison was **PARTIAL**:
manufacturing lagged the fixed peers while the selected electricity-price
change did not move in the preregistered support direction. It is descriptive
calibration only, with the old 2024 WDI fit overlap and missing Eurostat
observation-status flags disclosed. Five new country-disjoint WDI/WGI panel
holdouts yielded one **SUPPORTED** measured income/life-expectancy association
and four **PARTIAL** results. All five exclude the 40 old-fit countries,
apply the registered five-test family threshold, replay exactly, and receive
associational calibration only. The independently replayed PCW100 minimum-wage
association was also restored as descriptive calibration after a superseding
audit corrected literal errors in its earlier quarantine rationale. Its 17
post-result school links remain visible but untested and unscored; every school
aggregate is unchanged.

Two new country-disjoint WITS trade tests and eight new WDI/WGI panel tests
were registered in separate earlier commits, then run and exactly replayed.
All ten returned **PARTIAL** under their fixed family thresholds. The WITS
tests had 2,098/123 and 1,414/118 complete country-year/country samples;
the eight panel tests had 1,674–3,862 pairs and 116–163 countries. Each is
only a narrow measured association in public calibration, with zero school
credit. The known old results, old-country exclusions, source hashes, and
measurement limits are in their preregistrations and result cards. In
particular, a government-effectiveness/electricity-access negative estimate
with p=0.0181 did **not** meet its eight-test p<=0.0125 refutation cutoff.

A fourth four-case country-disjoint panel batch used tariff, patent, WGI,
poverty, migration, and population vintages pinned to tracked manifests. All
four specs and steelmen were committed before value runs; the exact read-only
replay passed. Tariff level versus next-year real private-consumption-per-person
growth was **REFUTED** under the fixed four-test threshold (1,930 pairs, 114
countries, positive coefficient 0.0001383, p=0.00366 against the expected
negative sign). Patent applications versus high-tech export-value growth and
regulatory quality versus poverty and net migration were **PARTIAL** (932/83,
954/60, and 3,546/163 pairs/countries). All are narrow descriptive
associations with zero school credit; the tariff result is not a causal claim
about tariff policy or welfare.

A fifth five-case country-disjoint measured panel batch was also registered
before values and exactly replayed. Government consumption versus next-year
private-credit depth (2,460 pairs/125 countries) and resident patent filings
per million (1,405/82), trade share versus resident patent filings per million
(1,422/82), WGI regulatory quality versus renewable installed-capacity growth
per million (3,501/158), and private-credit depth versus real income-per-person
growth (3,040/144) all returned **PARTIAL** under the fixed five-test
p<=0.02 family rule. Their source labels, measurement limits, old-country
exclusions, and zero school credit are frozen in the specs and result cards.

A sixth eleven-case country-disjoint measured panel family was registered
with its 15 pinned WDI/WGI source slices committed before value access. Its
preflight read country/year keys only; a feasibility screen had inspected null
masks but no candidate magnitudes, signs, or estimates, and this limitation is
disclosed in every spec. All eleven complete-case fits passed the registered
400-pair/35-country/five-year floor and exactly replayed from the clean branch.
Ten returned **PARTIAL** under the family-wise two-sided p<=0.10/11 rule. The
negative tax-revenue-share to next-year fixed-investment-share association was
**REFUTED** by a positive coefficient (1,903 country-years/110 countries;
coefficient +0.254676, p=3.07e-12). Both measures are GDP ratios, so this is
a narrow descriptive association, not a tax-policy or welfare effect. The
entire family is calibration only with zero school-score credit.

Four further direct or country-disjoint tests were registered before values,
run, and replayed. The EIA state electricity-generation test was **REFUTED**:
5 of 37 qualifying states with rising wind/solar generation had a lower coal
output on the frozen annual comparison, below its registered success floor. The
national BLS food-services/manufacturing payroll comparison was **PARTIAL**:
its +0.898499 percentage-point gap remained inside the fixed +/-1 point band.
The BIS nominal effective-exchange-rate/trade-share to next-year CPI panel was
**PARTIAL** (428 country-years, 20 countries; coefficient -0.84706,
p=0.01808 above the frozen 0.01 cutoff). All are measured calibration only,
with no causal, school, or policy-score credit. Their source vintages, meanings,
limits, and replay results are in the source-pinned specs and result cards.

The Peru-US 2009 treaty trade-flow design was **INCONCLUSIVE** because its
fixed-donor pretrend gap was 0.031993, exceeding the preregistered 0.03 cap.
Its policy record now links that test explicitly and excludes eight unrelated
automatic axis-overlap links; the browser and evidence indexes show zero tested
hypotheses and no treaty-effect credit. A separate fossil-subsidy/high-tech
export-share follow-up passed its fixed 247-pair/22-country sample floor and
returned **PARTIAL** (coefficient +0.074796, p=0.790246 against the frozen
negative 0.01 rule). Its first execution stopped before fitting because of a
nullable-year data-type error. The failed attempt was committed untouched;
a separately committed, byte-pinned erratum cast the same year keys to int64,
then the unchanged model was run and replayed. Both attempts remain inspectable.
This result is country-disjoint from the old fit but shares the World Bank/WITS
export measurement family, so it is not independent source replication. It is
calibration only with zero school or policy-score credit.

A separate Argentina core-CPI follow-up was registered and run locally, but
its full pinned fetch manifest contained unrelated local home paths. The
public-integrity gate rejected that source packet. Its spec, source, runner,
and result were removed from this review tree and **are not counted** in the
444 public records. The original local run remains available for a separate
administrative-redaction audit; post-result redaction cannot be presented as
an untouched prospective registration. No causal or school-score credit was
assigned. The local Git history still contains the rejected manifest in
its original commit; this branch must not be pushed or published before a
separate history cleanup and independent integrity review.

A separate legacy sign audit found 64 current generic-rule panel records and
57 historical-to-stored inferred-direction changes. The old text parser could
mistake `p<0.10` for a negative coefficient condition; future runs now fail
closed on that generic unpinned sign until a direction is explicitly supplied,
while old result artifacts remain unchanged pending manual
claim-by-claim adjudication. Five earlier calibration-only geographic holdouts
now have an explicit external school-score exclusion so later links cannot
silently award credit; their frozen runs remain untouched.

The regular registration, evidence-tier, funnel, census, school outcome,
second-order, and link audits were refreshed after the combined results. The
500-case prospective queue is a **design-review selection**, not a graduation
count. Its old same-commit results cannot be turned into strict registrations
by relabeling.

There are **215 verified archived** records in the current funnel. Even the
unrealistic upper bound of converting every one would yield 659 public
records, still **213 below** 872. The archive repair review found 131
near-zero placeholder cases using an outcome as its own control and a proxy
treatment; those need materially new designs, not cosmetic fixes. Peru's
frozen estimator and Paraguay's rule remain ambiguous, so direct promotion
was rejected. Reaching the 500 increment requires a substantial new wave of
individually specified, source-custodied strict registrations and successful
replays; current evidence does not justify claiming it has happened.

A current frozen-repair audit found **no immediately runnable** same-ID case
among the 215 verified archives. A separate metadata-only screen of the 820
legacy cases beyond the first 500 review rows found 67 distinct source-pair
groups as an upper bound for design review, including the five earlier
measured holdouts and the ten new follow-ups run in this sprint. Pair
membership creates no credit; the remaining groups still need claim-specific
source, holdout, and method checks. A wider metadata-only screen of all 1,320
legacy same-commit rows found at most 84 distinct, unregistered source-pair
groups passing a basic panel eligibility screen. Fifty-two still carry proxy
warnings, 17 use constructed or trend treatments, and only eight are simple
measured pairs without those or Fraser/Heritage flags. The 372 Heritage
cross-section rows reuse just 16 outcome-source pairs. These are design-review
ceilings, not conversions. Even converting all 215 archives and all 84 groups
would add only 299, leaving 129 of the requested 428 additions; in reality
neither full conversion is justified. A future batch must deduplicate semantic
aliases and use one family-wide multiplicity budget before reading outcomes. Alias-aware review also rejected apparent
new groups already represented by strict registrations, and sign-history
review rejected several legacy verdicts as design inputs.

No push, merge, or deployment is part of this status.
