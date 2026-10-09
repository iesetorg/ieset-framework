# Hypothesis conversion target status — 2026-10-10

The requested increment is **500 additional public hypotheses** above the
audited starting count of 372, so the target is 872. The current live evidence
gate reports **476 public of 2,022 hypotheses**: 51 featured and 425 calibration.
This is **104 additional** and leaves **396** to target. The 226 verified
archives remain archived. A public calibration is a completed, reviewable test,
not a supported, causal, policy-effect, or school-score finding.

## New prospective family

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
trade-opening step. The authored national drift map remains **1846–2026**, 145
countries, and 21 axes. These coding repairs do not confer empirical support.
See `engine/audits/policy_axis_source_corrections_2026-10-10.md`.

## Remaining work and source boundary

A fresh archive review found **no same-ID conversion** that clears its current
frozen specification with local data. In particular, the pinned Canada 2025
GDP-per-person holdout has no 2025 values, and a candidate Anglo money series
has no Canadian 2019–2024 values. Bulk event multiplication is also unsupported:
although the policy registry has 3,372 records, most lack the unit coding,
overlap control, and source/date custody needed for separate public tests. The
next measured prospects are a new OECD statutory corporate-tax-rate family
against Eurostat business R&D intensity and World Bank net FDI, followed by
an OECD labour-spending/migrant unemployment-gap design if its source and
sample checks pass. These are queues, **not counted graduations**. A WHO
particulate-matter/chronic-outcome lead was rejected before registration
because its short modeled window and concentrated exposure leave a weak test.

Generated preregistration, evidence, census, conversion-funnel, school,
second-order, and policy indexes were refreshed after the four results and
policy correction. Publication remains on hold: this local branch history
contains an older rejected, path-bearing source manifest followed by a
revert. No push, merge, or deployment is authorized by these local audits.
