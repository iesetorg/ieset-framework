# Hypothesis conversion target status — 2026-10-10

The requested increment is **500 additional public hypotheses** above the
audited starting count of 372, so the target is 872. The current local evidence
gate reports **546 public of 2,104 hypotheses**: 51 featured and 495 calibration.
This is **174 additional records** and leaves **326** to the record-level target. These
records are not independent research questions: one age-by-sex employment family
contributes 20 visible records. The family accounting below keeps that distinction
explicit. Another 238 records
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

## Latest locked family results

The three-test IMF inflation calibration was registered in `4c17b8e44f0a6c884c5b666aef0dabacaba63a3a`,
source-locked in `4a84a9e0eeacb0caca749b15f83f0f2804131bce`, and measured in `d0fbfd77f39004a56355e5a11b74841bc970bce6`. All three passed
method floors and were exactly replayed as public **PARTIAL** descriptive
calibrations: real household consumption/person β −0.00881024 (p=0.388457;
2,762 pairs/140 economies), fixed investment share β −0.697125 (p=0.127753;
3,105/153), and unemployment β +0.301462 (p=0.029461; 3,679/173).
The unemployment nominal p is below 0.05 but does not pass the frozen
three-test Bonferroni p≤0.003333 gate. None is an IMF-policy effect or earns
causal, policy, school, or featured credit. See
`engine/audits/imf_inflation_macro_responses_results_2026-10-10.md`.

The separate claim-specific tax/labour family was registered in `550a49fe5c54f9570e5308b03f1488b407565baf`,
source-locked in `c6970d0ea3bf98fcb12ca0c226b73f874330e9c2`, and measured in `8ddeeed681cc37512fe082029cfa28839a889fdf`. The tax measure
returned a public **PARTIAL** association (β +0.622553, p=0.11678; 775
pairs/50 economies). The labour-protection measure was **INCONCLUSIVE**:
its largest country supplied 18.218% of residualized treatment variation,
above the frozen 12% cap. The estimate is kept in diagnostics rather than
promoted. Both old generic Fraser/GDP-per-person placeholders remain archived.
Neither new case receives causal, policy, school, or featured credit. See
`engine/audits/placeholder_claim_specific_replacement_results_2026-10-10.md`.

Three observed Internet-uptake tests were registered in `115c5037d021716c00d7b0845fcca898f4e419c2`,
source-locked in `c594bfc524d39e6355e32c005efb2a0ab6dda135`, and measured in `ebf5c8d0df226568fa57ad531c31f1bcea861412`. All three had
ample complete rows and material uptake, but failed the same frozen
residualized-treatment year-concentration cap of 20%: business registrations
22.815%, services employment share 21.460%, and high-tech export share
27.310%. They are **INCONCLUSIVE** with no publishable coefficient; exact
replay passed. Internet uptake was an observed proxy, not a policy treatment.
See `engine/audits/wdi_digital_diffusion_structure_results_2026-10-10.md`.

The direct union-density/low-education-unemployment component was registered
in `f869983bd50a8ce7260380b506f3cee2f2a00c46`, source-locked in `a010eac8f12dc3f53a2e17967f37a5fd62edda5c`, and measured in `0c740f0a46f35ba734dddffce9e6eebe657313a5`.
Only 137 of 200 key-only windows had qualifying actual-status outcome pairs;
the frozen minimum per anchor and within-country union-range gates failed, so
no model was fit and the case is **INCONCLUSIVE**. Its eight artifacts replayed
exactly. The original multi-part union-density placeholder, youth and wage
compression components, and old verdict remain archived. These four
inconclusive tests added **zero** public calibrations.


The one-test gross-secondary-enrolment/fertility follow-through family was
registered in `a480a7942af078eb03fa5cf8d94798363787ee23`, source-locked in `5273d592bd4cbb50346668b5ca632f301b5439ae`, and measured in
`1b2b085a126b97e037f8383f8d1be23952e0ef9a`. All frozen complete-case, material-change, rank, and
concentration floors passed: 168 decade pairs across 72 countries, with 85
material schooling changes across 57 countries. Its association was public
**PARTIAL** (beta −0.000391181 ten-year log-fertility point per +1 enrolment
point; p=0.843036) and exactly replayed. The selected gross, both-sex
schooling measure is neither female completion nor an education policy
intervention. It receives zero causal, policy, school-score, position, and
featured credit. See
`engine/audits/wdi_secondary_enrolment_fertility_results_2026-10-10.md`.


The ten-test BIS household debt-service-change family against additional
OECD How's Life measures was registered in `7a92472731ebe9a00236495cdd37204cf99feccf`, source-locked in
`7b99e00e4ea5ac480718ce4dcefe43e383fe805a`, and measured in `d023e9c4401dc9cc67826cc271b46c99cc3718fe`. Nine tests passed the frozen
sample and method gates as public **PARTIAL** descriptive calibrations.
The youth not-in-employment-or-education measure was **INCONCLUSIVE**:
219 complete pairs fell short of its fixed 230-pair floor, so it received
no coefficient. All ten verdicts replayed exactly. None cleared the
family's p≤0.001 and practical-magnitude rule for a directional finding;
all causal, policy, school, position, and featured credit is zero. See
`engine/audits/bis_dsr_oecd_hsl_extended_results_2026-10-10.md`.

The twelve-test WDI real-GDP-growth family against mutually non-nested
Eurostat fuel-combustion CO2 source categories was registered in
`842ea1491f505205b5144b614e73779cbcfcd154`, source-locked in `48730de3ad0436351ea8e77c83e1e045e3eb8da7`, and measured in `a95d1739721cb4e41507da39a767067f0cabcbe9`.
All twelve passed frozen sample and concentration gates and replayed
exactly. Ten are public **PARTIAL** descriptive calibrations. Two passed
the fixed Bonferroni p≤0.0008333 and β≥0.005 thresholds as descriptive
**SUPPORTED** associations: other manufacturing/construction fuel
(β +0.0158829, p=0.0000716; 641 pairs/28 countries) and road transport
fuel (β +0.00749382, p=0.000000846; 664/29). Same-year aggregate GDP growth
is not a sector output or policy intervention, and the selected inventory
has no retained cell flags. All causal, policy, school, position, and
featured credit is zero. See
`engine/audits/wdi_gdp_eurostat_sector_co2_results_2026-10-10.md`.

The twenty-cell real-GDP-growth and OECD age-by-sex employment family was
registered in `b6aa15c2f6b118eb9db8b6e98ad1d43f538d8a58`, source-locked in `270134c36cd95c17b8a348462e599098ced2e8aa`, and measured in
`d39121ad74022bfcb58070d749f1322a65a5b427`. All 20 disjoint population cells passed the fixed sample and
influence gates, with 1,092 country-year pairs across 50 economies per cell.
Eleven cell estimates cleared the 20-test Bonferroni and effect-size rule as
descriptive **SUPPORTED** associations; nine are **PARTIAL**. Exact replay
passed. These are one correlated labour-market question, not 20 independent
confirmations or policy effects. They have zero causal, policy, school,
position, and featured credit. See
`engine/audits/wdi_growth_oecd_lfs_age_sex_results_2026-10-10.md`.

The BIS nominal effective-exchange-rate depreciation to Eurostat annual HICP
consumer-group test was registered as **one omnibus hypothesis** in
`682ad0d9b7a6d1ace1d1044643145c09badc0560`, source-locked in `62f821394631e384c3d025415f1eba9adcc4489e`, and measured in `60884324cffb20343eee88c87818166f56f6bac4`.
All 20 non-nested groups were estimable; five met the frozen positive
component rule (two-sided p≤0.0005, effect and country-deletion floors),
none met its opposite rule, and 15 were partial. The fixed omnibus rule
therefore returned descriptive **SUPPORTED**, with exact replay. The 20
component estimates count as one public record and do not identify causal
exchange-rate pass-through. Causal, policy, school, position, and featured
credit is zero. See
`engine/audits/bis_neer_eurostat_goods_hicp_results_2026-10-10.md`.

Record and family counting differ. Through the 524-record checkpoint, 148
identifiable gross additions mapped to 57 preregistered family/test labels;
three older ILO records were withdrawn. The starting 372-record snapshot lacks
an ID-level ledger, so a precise net count of new independent questions is
not recoverable. Related multi-outcome batches and the 20 employment cells
must not be represented as independent replications. See
`engine/audits/public_record_family_accounting_2026-10-10.md` and
`engine/audits/large_family_feasibility_and_acquisition_2026-10-10.md`.

## Latest historical and policy-event screens

Five new-ID, source-pinned tests were registered before their selected outcomes
were read. The pre-1980 JST credit-boom to crisis-onset test passed its source,
sample, and incident-event floors and returned **PARTIAL**: forward crisis
onset was 7/35 (20.0%) among high-credit anchors and 24/131 (18.32%) among
other at-risk anchors. Its risk ratio 1.092 and risk difference 1.68 percentage
points fell short of the frozen support thresholds of 2 and 2 percentage
points. This is **one** public descriptive calibration, with no causal,
policy, school, position, or featured credit. The licensed local JST R6 value
rows were not committed; the metadata lock and six aggregate run artifacts
replayed exactly. See `engine/audits/jst_pre1980_credit_crisis_2026_result.md`.

Four other preregistered tests stopped at frozen gates and add **zero**
public records. The Mexico–EU4 BACI comparison missed its pretrend gate
(absolute slope 0.088750 versus 0.03); the Ecuador–EU five-destination
comparison likewise missed its pretrend gate (0.075364 versus 0.03). The
2025 OECD bargaining/unemployment holdout had 22 actual-status complete
countries against its minimum of 24. The WITS tariff-duration two-real-outcome
test had 51 complete countries but only five with at least two high-tariff
years against a minimum of ten. No frozen gate was relaxed or alternate
post-result sample chosen. The direct treaty tests are descriptive only and
do not award policy-effect credit. See their individual result audits under
`engine/audits/`.

The reverted Argentina core-CPI holdout was audited retrospectively. Its
historical arithmetic reproduced, but its first registration had pinned a
full fetch manifest containing unrelated local paths. Those bytes cannot be
redacted without changing the frozen custody lock after outcome access. It
remains excluded from the public count; see
`engine/audits/argentina_core_cpi_provenance_review_2026-10-10.md`.

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
movement or a drift step. The scored national movement grid now spans
**1789–2026**, 145 countries, and 21 axes. Narrow French provincial-
privilege abolition (legally operative 3 November 1789), Civil Code (1804),
and Restoration Charter (1814) candidates each add a source-backed weak
`institutional.rule_of_law` step. They do not change France's statist
composite; the earliest composite step in any country remains 1846. Two newly sourced,
unlinked candidate UK policy records document the operative 1802 Parish
Apprentices Act and 1815 Corn Importation Act without inventing movement
scores. The drift page keeps both U.S. 1789 policy-only markers and the cited
1802, 1815, 1833, and 1844 policy-only markers visible and separately plots the early French rule-of-law
axis. These coding repairs do not confer empirical hypothesis support. See
`engine/audits/policy_axis_source_corrections_2026-10-10.md`,
`engine/audits/euro_schengen_axis_timing_corrections_2026-10-10.md`,
`engine/audits/uk_revenue_act_1869_policy_gap_2026-10-10.md`,
`engine/audits/french_pre1846_signed_backfill_2026-10-10.md`, and
`engine/audits/fr_1789_privilege_backfill_2026-10-10.md`, and
`engine/audits/us_judiciary_act_1789_policy_only_2026-10-10.md`.

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

An earlier archive review found **no same-ID conversion** that cleared its
frozen specification with local data. Of 233 verified archives then, 155 failed the
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
multiplication is also unsupported: the current registry has **3,382**
policies, but only **7** have a comparative structure declared, **3,359**
need treated/comparison unit coding, and **1,309** need exact event dates.
Six of those seven declare known measurement gaps; the seventh lacks an
outcome measurement plan. None is a verified causal estimate. The second-order
index now retains **3,366** policies,
including all **23** explicit evaluation designs even when a policy has no
scored drift axis. A WHO particulate-matter/chronic-outcome lead was rejected
before registration because its short modeled window and concentrated
exposure leave a weak test. WHO/JMP annual urban-sanitation and UNDP annual
expected-schooling change designs were also rejected before registration
because the selected vintages cannot identify independently measured annual
changes at the required country-years. The 1,320 legacy same-commit
registrations cannot become strict by renaming old results; new source-pinned
holdouts would need separate v2 registrations and measured runs.

The requested +500 remains unmet: **326 more public records** would be
needed, and the record count itself overstates independent research questions.
A separate feasibility audit found no defensible hundreds-sized family in the
preserved corpus. Priorities for genuinely new source acquisition are matched
regional wage/outcome panels, electricity price and reliability histories,
cohort mobility outcomes, wealth-tax behaviour, and technology-specific
renewables costs. Existing failed gates cannot be repaired by relabeling
old runs or multiplying outcome slices.

An independent drift check confirmed the current map spans 1789–2026, 145
national country keys, and 21 axes, with the first French weak rule-of-law step
in 1789 and the first statist composite step in 1846. A separate movement
vintage builder could previously encode California and EU-wide movements as
national country values and started its dense grid at 1800. Its loader and
builders now filter to national scope and begin no later than the earliest
authored national movement. The 108 old May-16 source-pinned vintages were
not silently overwritten; any refreshed vintage needs a new version and
dependent-run review.

Generated preregistration, evidence-tier, census, and conversion-funnel
indexes were refreshed after the latest frozen runs. Current local checks
passed: **6,246** specs and cross-references, 784 strict and 1,320 legacy
registration pairs, the 546/2,104 evidence and census checks, drift
consistency, 11 focused Python tests, eight web tests, TypeScript checking,
the **8,544-route** static site build, exact replay of the JST, tariff,
Ecuador, OECD, and Mexico packets, and public-tree OPSEC scanning. The
static drift and JST result pages were present in the build. The JST
post-result local-path redaction passed exact replay without changing
analytic rules; it does not erase path-bearing Git history. Publication
remains on hold because this local branch history also contains an older
rejected, path-bearing source manifest followed by a revert. No push,
merge, or deployment follows from these local audits.
