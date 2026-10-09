# Hypothesis conversion target status — 2026-10-09

The user's latest target was **500 additional public hypothesis records**.
The public evidence ledger had 372 at that point, making the target 872.
After the bounded repair and prospective batches in this sprint, the audited
ledger has **420 public records** (51 featured, 369 calibration) among 1,954
hypotheses. That is **48 additional** relative to the 372 starting point and
**452 short** of the requested increment. No result was made featured by
loosening its gate.

The latest four new-ID tests illustrate the decision boundary:

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

There are **214 verified archived** records in the current funnel. Even the
unrealistic upper bound of converting every one would yield 634 public
records, still **238 below** 872. The archive repair review found 131
near-zero placeholder cases using an outcome as its own control and a proxy
treatment; those need materially new designs, not cosmetic fixes. Peru's
frozen estimator and Paraguay's rule remain ambiguous, so direct promotion
was rejected. Reaching the 500 increment requires a substantial new wave of
individually specified, source-custodied strict registrations and successful
replays; current evidence does not justify claiming it has happened.

A current frozen-repair audit found **no immediately runnable** same-ID case
among the 214 verified archives. A separate metadata-only screen of the 820
legacy cases beyond the first 500 review rows found 67 distinct source-pair
groups as an upper bound for design review, including the five earlier
measured holdouts and the ten new follow-ups run in this sprint. Pair
membership creates no credit; the remaining groups still need claim-specific
source, holdout, and method checks. Alias-aware review also rejected apparent
new groups already represented by strict registrations, and sign-history
review rejected several legacy verdicts as design inputs.

No push, merge, or deployment is part of this status.
