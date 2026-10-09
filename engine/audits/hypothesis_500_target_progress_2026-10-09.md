# Hypothesis conversion target status — 2026-10-09

The user's latest target was **500 additional public hypothesis records**.
The public evidence ledger had 372 at that point, making the target 872.
After the bounded repair and prospective batches in this sprint, the audited
ledger has **472 public records** (51 featured, 421 calibration) among 2,018
hypotheses. That is **100 additional** relative to the 372 starting point and
**400 short** of the requested increment. Here public includes calibration;
featured remains 51, so the featured-only increment is zero. No result was
made featured by loosening its gate.

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

Three further direct or country-disjoint tests were registered before values,
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

A new male age-25-to-54 remittance/LFP follow-up repaired the endpoint of an
archived old run that had averaged ILO sex and age cells despite naming that
subgroup. Its fixed 148-area, 3,220-pair holdout passed the preregistered
sample floor and returned **PARTIAL** (coefficient -0.086589, p=0.109493;
99.375% family interval [-0.235777, 0.062599]). The series is an ILO
modelled estimate and can use World Bank/IMF macro inputs, so it is not
independent survey validation of its WDI predictors. This is descriptive
calibration only, with no causal, policy, or school credit.

A wider ILO source-dimension audit found three public calibration cards whose
saved results did not justify their stated endpoint or full decision rule:
`minimum_wage_youth_unemployment_tradeoff`,
`unemployment_benefit_generosity_employment_drag`, and
`workfare_conditionality_employment_effect`. An external integrity hold now
withdraws their public visibility and school-score eligibility without
rewriting historical specs or runs. The first two have invalid named primary
outcomes; workfare has a narrower measured primary but untested secondary,
age, timing, and robustness requirements. The source-key proof, eight already
archived ILO outcome cases, and prospective repair gate are documented in
`engine/audits/ilostat_dimension_integrity_2026-10-09.md`.

A separate Argentina core-CPI follow-up was registered and run locally, but
its full pinned fetch manifest contained unrelated local home paths. The
public-integrity gate rejected that source packet. Its spec, source, runner,
and result were removed from this review tree and **are not counted** in the
public records. The original local run remains available for a separate
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

The latest source-custodied wave added ten prospective tests, each registered
before outcome values were run. Four entered public **calibration** after exact
source and result replay: BIS real residential property-price change versus
next-year real GDP-per-person growth (**PARTIAL**, 542 pairs/25 held-out
countries); Korea–US 2012 directed trade flow (**SUPPORTED** under its fixed
pretrend and contrast floors); OECD youth median minimum wage versus next-year
unemployment (**PARTIAL**, 160 country-years/32 countries); and WGI regulatory
quality versus next-year electricity access (**PARTIAL**, 3,595 pairs/161
countries). The BIS p=0.00246 misses its 84-screen family cutoff 0.00119;
the youth and electricity estimates also miss their frozen cutoffs. None
establishes a causal effect, state-law treatment, or school-score credit.
Chile–US, Colombia–US, New Zealand–China, Australia–China, Australia–Korea,
and Australia–Japan treaty-flow cases remain **INCONCLUSIVE** after their
registered pretrend checks and stay archived. Their archived results are not
counted as public conversions.

The registration, evidence-tier, funnel, census, school outcome,
second-order, and link audits were refreshed after the combined results.
The three integrity holds removed 18 links from public tested coverage while
leaving every school net score unchanged; structural claim links do not
override an external evidence hold. The
500-case prospective queue is a **design-review selection**, not a graduation
count. Its old same-commit results cannot be turned into strict registrations
by relabeling.

There are **226 verified archived** records in the current funnel, including
the new inconclusive Vietnam WTO flow case. Even the unrealistic upper bound
of converting every one would yield 698 public records, still **174 below**
872. The archive repair review found 131
near-zero placeholder cases using an outcome as its own control and a proxy
treatment; those need materially new designs, not cosmetic fixes. Peru's
frozen estimator and Paraguay's rule remain ambiguous, so direct promotion
was rejected. Reaching the 500 increment requires a substantial new wave of
individually specified, source-custodied strict registrations and successful
replays; current evidence does not justify claiming it has happened.

A current frozen-repair audit found **no immediately runnable** same-ID case
among the 224 archives it inspected before the Vietnam case was added. A
separate metadata-only screen of the 820
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
ceilings, not conversions. The fossil and remittance follow-ups consumed two
of those eight simple-pair leads; subsequent source-pinned tests consumed more
of the plausible measured frontier. The remaining source-pair screen does not
supply hundreds of independent, registration-ready designs. A future batch must deduplicate semantic
aliases and use one family-wide multiplicity budget before reading outcomes. Alias-aware review also rejected apparent
new groups already represented by strict registrations, and sign-history
review rejected several legacy verdicts as design inputs.

An earlier read-only source inventory found 35 raw parquet vintages and 45
derived panels **in this isolated checkout**. That was a checkout-scope limit,
not an IESET corpus limit: the untouched main checkout holds 1,926 ignored raw
parquet vintages. Exact-SHA-pinned copies of the WID wealth file, a
profit-shifting vintage, the CEPII Gravity raw source, and twelve CEPII exposure
series were recovered into this isolated checkout without changing the main
checkout; it now has 67 raw parquet vintages after additional pinned WDI/WGI,
OECD, and V-Dem sources were restored. A committed single-vintage
recovery tool checks HEAD manifest pins and defaults to a dry run. These files
open source and key-only design review, but do not make any frozen archive
automatically runnable or public. The straightforward measured WDI/WGI, BIS,
OECD, ILO, and EIA pairs have already been used in strict v2 families. A WID
Sweden wealth-tax design was rejected before registration because the 2007
repeal also ended individual wealth-statistics collection, making a break in
the top-share series inseparable from a measurement change. The existing policy
record now distinguishes the December 2007 legislative decision, January 2008
commencement, and retroactive 2007 tax-year application. The profit-shifting
panel's named TWZ and CbCR windows remain short. Six of seven earlier
source-custodied treaty-flow candidates failed their frozen pretrend gate.

A seventh five-case country-disjoint WDI/WGI family was registered with exact
source pins, old-fit country exclusions, and a five-test p<=0.02 rule before
outcome fits. The five measured pairs were government consumption versus
next-year WGI corruption control, central-government tax-revenue share versus
next-year real household consumption growth, WGI regulatory quality versus
next-year internet use, WGI government effectiveness versus next-year gross
secondary enrollment, and WGI regulatory quality versus next-year physician
density. All five passed their complete-case floors and exact replay, but all
were **PARTIAL** under the frozen family rule. They enter public calibration
only, with no causal or school-score credit; the old proxy claims were not
validated. A separate Vietnam 2007 WTO directed-flow registration cleared
source and replay checks but was **INCONCLUSIVE** because its pretrend slope gap
was 0.083339 log units/year against the fixed 0.03 cap. It remains archived,
with no policy-effect credit. Its custody addendum records that a failed
pre-result extraction materialized flow text in process memory before a
key-census correction, although no magnitude was parsed, printed, used to
choose the correction, or evaluated before the frozen result run.

An additional WGI regulatory-quality to BIS real residential-price-growth
country holdout was independently registered and source-locked before its
value run. It had 542 complete pairs in 25 countries with no overlap against
the old 40-country fit rosters, and its exact replay passed. Its country-clustered
coefficient was -1.385916 with p=0.628738 against the frozen 84-screen
p<=0.001190476 cutoff. It is **PARTIAL** and enters public calibration only;
it does not validate a causal housing, affordability, policy, or school claim.
The OECD ALMP/EPL 2020–21 temporal holdout was then registered, source-locked,
run, and independently replayed. Its 34-country, 68-pair interaction was
negative (p=0.00731 against the frozen 0.01 cutoff), so the narrow measured
association was **REFUTED**. Pandemic confounding precludes a policy-effect
claim; it enters calibration with no school credit. A four-test OECD SOCX
programme family used measured health, family, old-age, and housing spending
against matched next-year outcomes with a family p<=0.025 rule. All four passed
their floors and exact replay. Health, family, and housing were **PARTIAL**;
the old-age spending to elderly relative-poverty association was **SUPPORTED**
(459 observations in 37 countries, p=0.0202), still descriptive calibration
only. Two distinct V-Dem/WDI country holdouts also passed registration,
source pins, data floors, and exact replay: women's movement freedom to female
labour-force participation (56 countries, p=0.197) and public-goods spending
composition to under-five mortality (57 countries, p=0.750). Both are
**PARTIAL** descriptive calibration, with no school or policy-effect credit.
Three CEPII Gravity exposure to WDI outcome tests were separately registered,
source-locked, and replayed with an old 61-country roster excluded and a
three-test p<=1/60 rule. All passed their complete-case/variation floors:
foreign market potential to next-year trade-openness change (4,674 pairs/122
countries, p=0.367), FTA gravity market share to private-investment change
(1,310/69, p=0.344), and FTA partner-GDP share to high-tech export share
(1,145/104, p=0.581). All three are **PARTIAL** descriptive calibration, not
independent treaty-event replications and not policy-effect evidence.

The integrity-detector scan found 36 flagged runs; all are legacy same-commit
registrations, so correcting a detector classification cannot graduate them.
A narrow detector repair now distinguishes missing source hashes from repeated
hashes and collapses multiple series from one publisher. The flags remain
excluded by their independent registration gate. A CEPII Gravity RTA label
cross-check found that its version-specific archive label file supports the
existing builder's category mapping, despite contradictory prose documentation;
no result depends on that RTA count and no source value was changed.

Five further measured hypotheses used three additional preregistration,
source-lock, and result commit sequences, each followed by an exact independent
replay. Two asked about WIPO patents, OECD manufacturing productivity, and
WDI high-tech exports; two paired OECD manufacturing unit labour costs and
Eurostat foreign-country/stateless arrivals with separate export-share and
income-inequality outcomes; one paired Eurostat business R&D intensity with
the future employment rate of tertiary-educated adults. All five passed
sample and estimator floors but returned **PARTIAL** under their frozen
family or single-test thresholds. The immigration variable is citizenship
based, not foreign-born; the Gini outcome has a survey/income reference lag.
All five are descriptive public calibration with no causal, policy-effect,
featured, or school-score credit. The registration audit now finds 698 strict
pairs, 1,320 legacy same-commit pairs, and no unpaired specs.

Five more source-custodied tests entered public **calibration**, each after a
separate registration and source lock and an independent measured replay:
Eurostat business R&D versus next-year WIPO resident patenting (PARTIAL;
655 country-years/32 countries, p=0.0404 against a 0.005 cutoff); CEPAL
national poverty versus next-year IMF inflation (PARTIAL; 281/14, p=0.727);
Atlanta Fed low-minus-high wage-growth quartiles (PARTIAL; mean -0.30
percentage point over 32 fixed months); OECD top statutory personal income
tax versus next-year WID all-ages top-0.1% income share (PARTIAL; 688/30,
p=0.656); and CEPII RTA-covered partner expansion versus WITS exported HS6
product-count growth (PARTIAL; 169 event windows and 1,376 comparison
windows, p=0.830). These are measured or conditional associations, not
independent causal replications. None received policy, school, featured, or
causal credit. The CEPII/WITS frozen verifier has a Parquet array/list
comparison defect; its adjacent, separately committed erratum replays the
unchanged estimator and result exactly. The CEPAL result was relocated from
the dirty main checkout to this isolated branch with original commits and
source hashes retained in a custody audit; its narrow-lock replay adapter
passes without the unrelated path-bearing full fetch manifest. Three newly
used publisher namespaces were registered conservatively as pending reusable
fetchers; the exact raw/vintage pins, not a ready-fetcher claim, support
these local replays.

One further OECD migrant/native tertiary employment-gap versus employment-
protection test was registered, source-locked, and replayed, then remained
**INCONCLUSIVE**. All 265 selected country-years had valid values, but only
15 had the frozen minimum 0.05-point within-country protection-index change,
below the preregistered 20-row variation floor. No coefficient or public
credit was produced. A wider archive review found no immediately runnable
same-ID promotion among 225 checked records. The next ILO/OECD bargaining
candidate was stopped before outcome access because the OECD ERB field's
label conflicts with the coverage codebook and its stable sample is thin;
all six existing records citing that feed are already archive. BIS/WHO and
JST historical crisis leads were also left unregistered because of endpoint
or episode-comparability limits. These are design-review findings, not a
claim that every possible future corpus question has been exhausted.

The drift map now uses the full authored 1846–2026 movement span and 145
country series. Its national totals exclude California's subnational movement
and five EU-wide programmes whose member applicability is not yet coded.
The atlas slider reaches 1846, and all 145 countries can be picked individually.
Source-reviewed duplicate coding was removed from the UK 1976, US Biden, and
Colombia 2002 umbrellas, then from overlapping Obama, Trump, Thatcher,
Doi Moi, and Mulroney/Chrétien movements. Brazil's Plano Real and Mexico's Banxico/Article 27
overlaps were also corrected; the duplicated US Inflation Reduction Act policy
was consolidated under one dated record. The EU-wide source movements remain
in the corpus and atlas; a separate drift layer needs a member, date, and
overlap rule before those steps can enter national comparisons. These map
and policy repairs do not confer empirical support on linked hypotheses. A
second source-reviewed wave corrected overlapping or backdated steps in
Canada, China, Czechia, Ecuador, El Salvador, France, Germany, India,
Ireland, the Netherlands, New Zealand, the UAE, the UK, and Vietnam. National
umbrella and successor records no longer duplicate the reviewed policy
decisions; uncertain credit rescues, political tax commitments, savings-fund
asset transfers, and unsupported omnibus tax claims retain contextual records
without scored drift. A mechanical overlap screen still has unresolved
candidates, so the displayed historical totals remain reviewable estimates,
not a claim that every national attribution has been exhaustively adjudicated.
Three source-verified Swiss candidate records were added for the 1992 EEA vote,
the 2001/2003 debt brake, and the 2011–2015 SNB euro floor; the policy registry
now has 3,372 records and 47 permitted candidate forward references after
three source-checked Czech records and one El Salvador budget record.
Dodd-Frank, ARRA, and USMCA policy axes and dates were also narrowed to source-supported
provisions. The three Swiss date-only candidates have no coded axis movement;
the policy quality audit flags them as thin rather than inferring effects.
An additional five-country overlap pass removed Canada's unenacted capital-
gains increase and withdrawal as opposite tax steps, stopped double scoring
Singapore's 1955 colonial CPF scheme as a PAP-era transfer/spending cut,
assigned Indonesia's Bank Indonesia independence to its May 1999 law once,
kept Ecuador's January 2017 EU trade step while withholding an unsupported
second 2017 Pacific Alliance step, and moved Japan's FY2026 budget axes from
the 2025 draft to 2026 enactment. Japan's interagency foreign-investment
review began operating in June 2026, so only a weak 2026 review step remains;
broader screening rules take effect in 2027 and no trade-openness change is
inferred. The source and record-level dispositions are in
`engine/audits/national_drift_overlap_corrections_2026-10-09.md`. The
regenerated map still has 145 countries, 21 axes, and a verified 1846–2026
range. Its scores remain authored decision coding, not measured effects.

FAO food-security designs remain a source-custody queue. Key-only screens found
up to three distinct nonoverlapping-period associations, but the large ignored
FAO parquet files lack tracked source-vintage pins and the annual-looking PoU
and FIES data are regional aggregates. They were not registered or counted.

Final source validation accepted 6,147 specs with 47 permitted candidate
forward references; link reciprocity had zero errors/warnings, scope validation
zero errors and seven existing warnings, drift artifact freshness passed, and
the current local web build rendered 8,359 static pages. Standard pytest collection
now resolves IESET's own scripts after adding a package marker. An earlier full
isolated-checkout run had 475 passed, 48 skipped, and 17 failures in older test
areas; several expect an absent checkout virtualenv, ignored raw vintages, or
release assets. Those failures need separate investigation and fixture/artifact
restoration before a full-green claim. All 30 focused drift and attribution
tests passed after the current wave; the full suite has not been re-run on
this snapshot.

No push, merge, or deployment is part of this status.
