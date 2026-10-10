# Hypothesis conversion target status — 2026-10-10

The requested increment is **500 additional public hypotheses** above the
audited starting count of 372, so the target is 872. The current live evidence
gate reports **480 public of 2,026 hypotheses**: 51 featured and 429 calibration.
This is **108 additional** and leaves **392** to target. The 226 verified
archives remain archived. A public calibration is a completed, reviewable test,
not a supported, causal, policy-effect, or school-score finding.

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
movement or a drift step. The authored national drift map remains
**1846–2026**, 145 countries, and 21 axes. No dated national movement or
policy record before 1846 exists in the authored corpus. These coding repairs
do not confer empirical support. See
`engine/audits/policy_axis_source_corrections_2026-10-10.md`,
`engine/audits/euro_schengen_axis_timing_corrections_2026-10-10.md`, and
`engine/audits/uk_revenue_act_1869_policy_gap_2026-10-10.md`.

## Remaining work and source boundary

A fresh archive review found **no same-ID conversion** that clears its current
frozen specification with local data. In particular, the pinned Canada 2025
GDP-per-person holdout has no 2025 values, and a candidate Anglo money series
has no Canadian 2019–2024 values. Bulk event multiplication is also unsupported:
the current registry has **3,373** policies, but only **5** are ready for a
comparative event design, **3,352** need treated/comparison unit coding, and
**1,309** need exact event dates. A WHO particulate-matter/chronic-outcome lead
was rejected before registration because its short modeled window and
concentrated exposure leave a weak test. WHO/JMP annual urban-sanitation and
UNDP annual expected-schooling change designs were also rejected before
registration because the selected vintages cannot identify independently
measured annual changes at the required country-years. A WDI business-
registration/tourism to OECD youth-employment pair is under key-only design
review and **not counted**. The 1,320 legacy same-commit registrations cannot
become strict by renaming old results; new source-pinned holdouts would need
separate v2 registrations and measured runs.

Generated preregistration, evidence, census, conversion-funnel, school,
second-order, and policy indexes were refreshed after the eight new results
and policy corrections. Publication remains on hold: this local branch history
contains an older rejected, path-bearing source manifest followed by a
revert. No push, merge, or deployment is authorized by these local audits.
