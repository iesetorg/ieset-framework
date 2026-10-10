# Hypothesis conversion target status — 2026-10-10

The requested increment is **500 additional public hypotheses** above the
audited starting count of 372, so the target is 872. The current local evidence
gate reports **498 public of 2,046 hypotheses**: 51 featured and 447 calibration.
This is **126 additional** and leaves **374** to target. Another 228 records
have verified registration but remain archived. A public calibration is a
completed, reviewable test, not a supported, causal, policy-effect, or
school-score finding.

## New prospective families

Four distinct BIS household debt-service-change to OECD How's Life outcome
changes were registered in commit `867fd75862c8235837c642c30463c0f010a25d8f`, source-locked in `235de008fb7bb57a64ab816368989efbc984d824`,
and measured in `86785f55ef94b80298965cb72c96f1a3a27d559f`. The selected raw vintages, key-only roster,
complete-case and exposure floors, country/year fixed-effects estimator, and
four-test Bonferroni rule were frozen before the selected OECD outcome values
or missingness were opened. All four passed those floors and returned **PARTIAL**:

| Outcome, adverse-oriented | Coefficient per 1-point DSR change | Two-sided p |
| --- | ---: | ---: |
| Difficulty making ends meet | +0.163952 | 0.555607 |
| Housing affordability (income remaining after housing costs, sign-reversed) | +0.0440897 | 0.478364 |
| Inability to keep home adequately warm | −0.188595 | 0.558996 |
| Negative affect balance | −0.0501715 | 0.553022 |

Each required p≤0.0025 and an adverse-oriented coefficient magnitude of at
least 0.25 for a directional conclusion. The results make no debt-service,
housing, or labour policy-effect claim. They have zero school, policy, causal,
and featured credit. The frozen runner's `--verify` encounters a Parquet
array/list comparison mismatch; separately committed adapter `01aa25bbe7fdbde0e04617a90a71f46b0ce80535`
normalizes that serialization in the read-only comparison and exactly replays
all four unchanged estimates and artifacts. See
`engine/audits/bis_dsr_oecd_hsl_family_results_2026-10-10.md` and the adjacent
replay erratum.

The two-test OECD combined statutory corporate-tax-rate change family was
registered in `3e3a79065d82ee6413c844cde117cba2eb13a2d2`, locked to exact OECD, Eurostat, and WDI sources in
`29fc9e578d9603ffa0c9b7d7ab75aff710949f5a`, and measured in `112f71178358e5dc869e5ce8931ffbfcdcc64fcb`. Both complete-case and material-tax-
change floors passed. Business-performed R&D/GDP returned beta −0.0000888
(two-sided p=0.9712; 565 pairs/35 countries), and net FDI inflows/GDP returned
beta +0.13015 (p=0.6191; 2,211 pairs/132 countries). Both are **PARTIAL** and
exactly replayed; neither supports a tax-policy effect. Their two-test
Bonferroni cutoff was p≤0.005 plus a prespecified practical magnitude. They
have zero school, policy, causal, and featured credit. See
`engine/audits/oecd_cit_berd_fdi_family_results_2026-10-10.md`.

The two-test public active-labour-spending and foreign-citizen-arrivals family
against the foreign-born minus native-born unemployment-rate gap was registered
in `a13d42d8f2a55fadedb4752d867f7c7379d177c6`, source-locked in `ee22abe5f6ae9786a38fc616654fc49581d5bfab`, and measured in `b2c51947a9adc5fd56735e93c81c4d49525db97f`.
Both primary sample and material-exposure floors passed. ALMP returned beta
+0.09816 gap points per +1 GDP-percentage-point spending change (p=0.4047;
621 pairs/34 countries). Arrivals returned beta +0.007137 gap points per one
additional arrival per 1,000 residents (p=0.8235; 462 pairs/26 countries).
Both are **PARTIAL**, below the frozen practical/significance gates, and
exactly replayed. The mandatory alternate Eurostat age selector and the
prespecified baseline and crisis-year diagnostics did not establish a stable
directional result. Neither is a programme or immigration-policy effect;
school, policy, causal, and featured credit remain zero. See
`engine/audits/labour_gap_family_result_2026-10-10.md`.

The two-test WDI business-registration/tourism family against OECD youth
employment was registered in `6a44ffa419e9f894bbecadfff2f8620ab9ef46d7`, source-locked in `208634557af960bc2675dd03fa9ef746e378ad8b`, and
measured in `57315d3b79f358c3b7189a4723851776309c7214`. Business registrations returned **PARTIAL**
(beta +3.03155 youth-employment points per log change, p=0.005935; 489
pairs/45 countries), missing the two-test p≤0.005 cutoff. Tourism arrivals
returned a descriptive **SUPPORTED** association (beta +3.38566, p=0.003253;
564 pairs/50 countries) under the frozen sample, practical-magnitude, and
family-significance gates. Both are public calibrations with zero causal,
policy, school, and featured credit. A post-result leave-one-country check
kept the tourism coefficient positive in all 50 refits, while four omissions
crossed the primary p≤0.005 cutoff; it does not alter the frozen verdict. See
`engine/audits/tourism_youth_employment_leave_one_country_2026-10-10.md`.

The two-test WDI real-GDP-growth family against Eurostat EU-SILC employed and
employee in-work-poverty-rate changes was registered in `bc1c7b551e2860e0ddae2c55eb75b3ee4b8841c7`,
source-locked in `297098acf9fb974cf13d3e7a6e046a75c09dad95`, and measured in `1845d7c2ac76b45d3ec1f4b58bdf14e255b080d1`. Both passed their
sample and material-exposure floors but returned **PARTIAL**: all employed
beta +0.0299563 poverty points per GDP-growth point (p=0.259448; 383
pairs/30 countries), and employees beta +0.0416935 (p=0.170615; 298
pairs/30 countries). The selected vintage lacks break flags; Ireland and the
United Kingdom were excluded for income-reference-period exceptions. Neither
supports a GDP-policy effect, and both have zero causal, policy, school, and
featured credit.

The two-test WDI electricity-exposure family against Eurostat public
electricity/heat CO2 was registered in `5fbe97627cf272d545ae4c8aa526bde18aa7f6dc`, source-locked in
`16bf872b330c9a00bc29dd1bdc0dfae1bbfdf624`, and measured in `e5cc790bcd5142c2a9d8dd0b79097f93af4bc6b3`. Both complete-case and material
exposure floors passed. Renewable-generation-share change returned **PARTIAL**
(beta +0.00273547 log CO2 per share point, p=0.11884; 873 pairs/29 countries),
as did electric-use-per-person change (beta −0.0486344 per log use change,
p=0.72400; 926/29). The prespecified pre-2019 diagnostics also failed the
directional family rule. Exact replay passed; neither is an energy-policy
effect, and both have zero causal, policy, school, and featured credit.

The two-test Internet-uptake and publicly performed R&D family against WIPO-
origin resident patenting was registered in `54632a7f60b7a5781f6048d59582829e137bf279`, source-locked in
`38fc024b233ed4565c292bf84927bae44f238c31`, and measured in `b0aac02e059951205cf93b9adaae7f54e6495bf2`. Internet uptake returned
**PARTIAL** (beta −0.0008447 log patent units per percentage point,
p=0.753589; 619 pairs/34 countries). Government-plus-higher-education
performed R&D/GDP also returned **PARTIAL** (beta +0.153955 per GDP point,
p=0.400313; 561/32). Both passed their frozen sample, material, and
concentration gates and exactly replayed; neither supports a causal
innovation or policy claim. All school, policy, causal, and featured credit
is zero.

The two-test OECD corporate-rate and top-PIT tax-cut family against next-year
WDI new limited-liability registrations was registered in `a18fccd902d89960144f909ad02f7b854748a754`,
source-locked in `dcdf4c7e959f99b890aaaa547f4586c809474de3`, and measured in `c630a102fe04e17e83983a8757e10f16a6f29eb3`. Both retained
all valid large tax changes using prespecified cut/hike categories. Corporate
rate cuts returned **PARTIAL** (beta −0.0212048 log registrations,
p=0.335424; 1,282 pairs/114 countries, 154 cut years); top-PIT cuts returned
**PARTIAL** (beta −0.0197594, p=0.450230; 391/35, 40 cut years). Both passed
the frozen sample, event, and concentration gates and independently replayed.
They are descriptive calibrations, not tax-policy effects, with zero causal,
policy, school, and featured credit.

## Additional prospective tests and frozen failures

Ten further tests were registered after the earlier wave, each with a separate
source lock and measured result commit. Eight cleared their sample and method
floors and entered the public **descriptive-calibration** tier as PARTIAL:
remittance growth against secondary enrolment and formal business entry (two),
public active-labour spending against low-education employment, real effective
exchange-rate appreciation against tourism, top personal-income-tax hikes
against disposable-income Gini, new CEPII free-trade partners against
manufactures export share, sustained FDI inflows against resident patenting,
and WGI government-effectiveness change against later exported-HS6 product
breadth. These are distinct source-pinned estimates, but neither the local
multiple-test cutoffs nor strict chronology corrects the wider archive-wide
selection history. None earns causal, policy, school-score, or featured credit.
The individual sample sizes, coefficients, and exact replay checks are in
their dated result audits and immutable run packets.

Two frozen tests stayed **INCONCLUSIVE**. The WGI-effectiveness to OECD
treatable-mortality test encountered an entirely null selected raw
`Observation value` column; a normalized `value` field exists, but substituting
it after the outcome was opened would violate the preregistered rule. The
wealth-tax-receipts to WID top-1 wealth-share test had 1,113 complete pairs
across 38 countries, but two selected values failed its prespecified 0–100
range gate; estimation therefore stopped before its influence or rank gates.
Neither inconclusive test enters the public count. The two latest packages
registered in `8df05e8174c62aa2450d1c051a16d3c364a893ee`, locked in `f349add954bbda5f84c0d6eeac5204e5289b5125`, and ran in `25872b98f9ecc9cacb58ede796c4b7a1befaf21b`;
their exact artifact replays passed. The WGI export-breadth coefficient was
−0.0414351 log1p point per WGI point (p=0.592705; 1,862 pairs/153 reporter
economies), below its frozen directional rule.

## Corpus and drift corrections

Source-backed policy correction `daad06ddec8283bf05cb213bf28f1f75d8587067` dated Bahrain's VAT law decision
in December 2021 and its standard-rate start in January 2022, then removed
unsupported personal-income-tax and spending axes. Its parent movement's four
axes were withheld because remaining child decisions occurred in 2021–2022
but would otherwise be backdated to 2020. Bahrain's false 2020-onward
tax-progressivity level changed from −2 to 0 and composite drift from −1 to 0.
Slovenia's euro decision/adoption dates were separated and its unsupported
trade and central-bank-independence axes removed; its displayed drift was
unchanged. The 1846 UK Corn Law record now cites the original statute and
states the phased tariff reduction accurately, retaining the supported
trade-opening step. Subsequent source-backed correction `ba561a3cc4e8d70721d29c5acfe444d4ec152724` removed
unsupported euro-as-trade, patient-fee-as-transfer, and generic rule-of-law
steps in Slovakia and Croatia; it put the retained Croatian border and labour
steps in their operative 2023 year. Only those two countries' derived scores
changed. Separate policy `32a11b8a48acba4ab87a02a814cfab4412be72f5` records the 1869 final cessation of UK
corn import duties from 1 June under the Revenue Act, without inventing a
movement or a drift step. The scored national drift map remains
**1846–2026**, 145 countries, and 21 axes. Two newly sourced, unlinked
candidate UK policy records now document the operative 1802 Parish Apprentices
Act and the 1815 Corn Importation Act. They carry no invented movement,
numeric drift step, or empirical support; the first defensible scored national
movement remains in 1846. The drift page now shows these cited policy-only
years as linked cards and dashed chart markers, with no scored values before
1846. These coding repairs do not confer empirical support. See
`engine/audits/policy_axis_source_corrections_2026-10-10.md`,
`engine/audits/euro_schengen_axis_timing_corrections_2026-10-10.md`, and
`engine/audits/uk_revenue_act_1869_policy_gap_2026-10-10.md`.

Finland correction `0811718366e3d5227347072564e1c724aff3113f` put the principal compulsory-education
extension in August 2021, the family-leave entitlement in August 2022, and
the climate and gas-supply steps at their documented 2022 dates. It removed
unsupported axes and a permanent 2019 fiscal-spending step based on a
temporary pandemic spike. All 30 changed derived country-year rows belong
to Finland; see
`engine/audits/finland_policy_drift_source_correction_2026-10-10.md`.
The composite map now starts each country line at its first scored valenced
axis step; 141 of 145 movement countries have such coding, while four retain
movement timelines without fabricated zero lines. A reviewed tone pass
corrected 66 text-triggered false authoritarian labels without changing any
numeric drift trajectory. Eight borderline labels retain their prior tag
pending a separate regime review. See
`engine/audits/drift_composite_coverage_tone_review_2026-10-10.md`.

## Remaining work and source boundary

A fresh archive review found **no same-ID conversion** that clears its current
frozen specification with local data. Of 228 verified archives, 155 fail the
estimator floor; 131 of those repeat a claim-mismatched Fraser-index/GDP-per-
capita placeholder. Eight plain missing-verdict records fail frozen coverage
floors or lack a prespecified non-support label, and the sole replication-only
case lacks the required measured outcome. These need new designs or genuine
reruns, not metadata promotion. Among 1,320 legacy same-commit pairs,
only 203 have complete old source pins, and just 22 have any confirmed added
raw calendar year in a later preserved vintage; those counts are upper bounds,
not ready conversions. See
`engine/audits/legacy_archive_v2_readiness_2026-10-10.md`. In particular,
the pinned Canada 2025 GDP-per-person holdout has no 2025 values, and a
candidate Anglo money series has no Canadian 2019–2024 values. Bulk event
multiplication is also unsupported: the current registry has **3,375**
policies, but only **7** have a comparative structure declared, **3,352**
need treated/comparison unit coding, and **1,308** need exact event dates.
Six of those seven declare known measurement gaps; the seventh lacks an
outcome measurement plan. None is a verified causal estimate. The second-order
index now retains **3,361** policies,
including all **23** explicit evaluation designs even when a policy has no
scored drift axis. A WHO particulate-matter/chronic-outcome lead was rejected
before registration because its short modeled window and concentrated
exposure leave a weak test. WHO/JMP annual urban-sanitation and UNDP annual
expected-schooling change designs were also rejected before registration
because the selected vintages cannot identify independently measured annual
changes at the required country-years. The 1,320 legacy same-commit
registrations cannot become strict by renaming old results; new source-pinned
holdouts would need separate v2 registrations and measured runs.

Generated preregistration, evidence, census, conversion-funnel, school,
second-order, and policy indexes were refreshed after all current result and
policy commits. Local checks passed: 6,178 specs and cross-references,
69 focused Python tests, eight web tests, TypeScript type checking, the
static site build, generated drift consistency, exact replay of the two latest
run packets, and public-tree OPSEC scanning. The static drift page and both
pre-1846 policy pages were present in the build. Link reciprocity had zero
errors or warnings; scope alignment had zero errors and seven warnings. Publication remains on hold: this local branch history
contains an older rejected, path-bearing source manifest followed by a
revert. No push, merge, or deployment is authorized by these local audits.
