# Public conversion source and packet screen — 2026-10-10

Read-only decisions from integration commit `2c24bc95e6ec11b280b136cb4a97f568d37a70f9` and its locally regenerated, still uncommitted evidence ledger. This audit adds **zero** public hypotheses and changes no frozen specification, registration, verdict, threshold, source, runner, claim link, or gate. Conflict, climate, and World Bank Enterprise Surveys families are assigned to other lanes.

## Census and immediate eligibility

The committed 10 October conversion funnel at this commit reports **2,267 hypotheses, 650 public, 296 verified archives, and 1,321 legacy same-commit first-action cases**. The shared integration checkout's newly regenerated local evidence ledger, not yet committed when inspected, reports **2,323 hypotheses, 706 public, 296 verified archives, 1,320 legacy same-commit archives, and one registered record without a run**. The 56 added public records in that local ledger must not be represented as published or counted a second time. Every one of the 296 verified archives still has at least one public exclusion:

| Sole recorded exclusion in regenerated local ledger | Verified archives |
| --- | ---: |
| Estimator floor failed | 154 |
| Non-result verdict | 91 |
| Canonical verdict missing | 8 |
| External integrity quarantine | 5 |
| Falsification rule unsharpened | 2 |
| Audit quarantine pending v2 | 1 |
| Multiple simultaneous exclusions | 35 |
| **Total** | **296** |

The eight sole missing-verdict cases and the apparent tariff replication-path case were already checked against their frozen rules in `verified_archive_nine_case_triage_2026-10-10.md`: the former contain coverage/weak-result blockers and the latter never measured its registered treatment and joint outcomes. A separate review found 131 Fraser/GDP-per-person placeholder fits in the 155-case estimator-repair queue; those fits do not measure their varied claims (`verified_estimator_nonplaceholder_screen_2026-10-10.md`). These are not metadata-only conversions.

## The apparent 51-case legacy cohort

The selected 500-case prospective-v2 review queue has **51 records with no *review flags***. Every one still has `legacy_same_commit` registration, so an old `SUPPORTED`, `PARTIAL`, or `REFUTED` label does not meet strict pre-run chronology. I parsed each old run manifest's `vintages` or `inputs`, accepting list or mapping forms, and verified named SHA-256 hashes against existing files in the user's main local checkout. This is source-byte custody for the **old run**, not a new held-out dataset.

| Old source-custody result among 51 | Cases |
| --- | ---: |
| Every listed path and SHA-256 matches a surviving main-local file | 22 |
| At least one source entry lacks a path/hash pin | 21 |
| Fully pinned, but at least one named source file is absent from the main checkout | 7 |
| Fully pinned, but current derived country-drift bytes do not match the old hash | 1 |
| **Total** | **51** |

Only `asian_convergence_vs_western_stagnation_2000_2023` has all its old listed source bytes present and hash-matched in the **isolated integration** checkout itself. The user's main checkout has 1,935 local vintage files; isolated integration has 55. Main-local availability requires an explicit, hash-verified restore or retained slice for an isolated new run. All 51 old run directories lack the current packet's frozen `hypothesis.yaml` copy. The current public gate's decisive blocker here is registration chronology; the packet gap also matters for a new prospective family.

The 22 main-local hash-matched old-source records are the exact **source review cohort**, not a graduation cohort:

- Seven country growth/health/services shifts: `albania_growth_health_services_shift_1990_2023`, `armenia_growth_health_services_shift_1990_2023`, `bangladesh_growth_health_services_shift_1990_2023`, `bhutan_growth_health_services_shift_1990_2023`, `cambodia_growth_health_services_shift_1990_2023`, `chile_growth_health_services_shift_1990_2023`, `china_growth_health_services_shift_1990_2023`.
- Five historical banking crises: `banking_crisis_brazil_proer_1995_1997`, `banking_crisis_mexico_tequila_1994_canonical`, `banking_crisis_south_africa_african_bank_2014`, `banking_crisis_turkey_2001_canonical`, `banking_crisis_vietnam_2012_2015_restructuring`.
- Ten other old questions: `top_1_percent_income_share_growth_drivers`, `argentina_cepo_lift_2015_fx_inflation_reserves`, `asian_convergence_vs_western_stagnation_2000_2023`, `german_manufacturing_va_decline_2017_2024`, `labour_market_flexibility_unemployment_duration`, `oecd_union_density_disposable_gini_panel`, `uk_furlough_2020_unemployment_output_shield`, `volcker_disinflation_output_recovery`, `wdi_business_entry_rule_of_law_growth_panel`, `wid_top_income_share_trade_openness_panel`.

These rows cluster around seven related country checklists and five event-specific banking crises; they are not 22 independent new holdouts. The old Asian-convergence result had its compound v1 falsification rule changed to a primary-only v2 after the first result, while the saved card both reports an insignificant conditional coefficient (p=0.720) and calls it significant in prose. Its surviving WDI file cannot repair chronology or the post-result rule. `wdi_business_entry_rule_of_law_growth_panel` already has a separate geographic-holdout v2 record. `oecd_union_density_disposable_gini_panel` already measures the inequality half of its old conjunction. The WID top-0.1-share record has a source through 2024 but its old panel covered 1996–2023, so one later calendar year alone is not a robust independent test. Historic 1995/2001 crisis and 1979–83 Volcker events have no automatic new event holdout. No count should be raised by splitting those records into correlated subgroups.

## Decision and required next step

**No bulk cohort is presently graduation-ready.** The 296 verified archives have substantive current exclusions; the 51 strongest-looking legacy records still require new prospectively committed IDs rather than repair of their old runs, and only 22 even pass this narrow old-source custody screen in the main-local corpus. A new v2 would need a claim-matched, independent holdout or genuinely revised estimand; fixed source-key roster, sample/coverage and influence floors, full family denominator and error rule; a specification commit before selected outcome access; a later source-lock commit; a later measured result with diagnostics, frozen hypothesis copy, manifest, evidence packet, result card and read-only replication; and exact replay plus public-ledger and claim-link review. Old coefficients, labels and packets confer no credit. No such new registration was made from this screen because the necessary independent outcome window and full design have not been established for a batch.

The highest-value next work is source acquisition for a direct, claim-matched holdout, then a small prospectively registered family with all correlated tests counted together. The 51 record list is a triage aid; source-byte availability, old run completeness, and group labels are neither identification nor proof that a new test can pass its frozen gates.
