# Legacy hypothesis conversion feasibility: 10 October 2026

This is a local source snapshot and a planning audit, not a batch graduation. It uses the temporary preregistration index and evidence-tier builder on branch `codex/ieset-agriculture-transition-forward` after its committed result. Other concurrently integrated branches may change the live total. The 9 October prospective-v2 review queue is a dated triage input, not a run ledger.

## Target arithmetic

| Source snapshot measure | Records |
| --- | ---: |
| All hypotheses in this branch | 2,152 |
| Public visible (531 calibration, 50 featured) | 581 |
| Archived | 1,571 |
| Archived with legacy same-commit registration | 1,320 |
| Archived with verified registration | 250 |
| Registered but no run | 1 |
| Public target under review | 872 |
| Gap from this branch's 581 | **291** |

Even if every one of the 250 verified archived records and the one registered/no-run record became public, this branch would reach only 832. **At least 40 additional new prospective cases** would still be needed; because most of those 251 are blocked by substantive gates, the realistic need is much larger. This is a mathematical lower bound, not a claim that those 251 can pass.

## What can be credited now

**Zero remaining archive records are proven ready for graduation without further case-level work.** Among the 250 verified archived records, the exact sole-reason breakdown is 154 estimator-floor failures, 47 non-result verdicts, 8 missing verdicts, 5 external-integrity quarantines, 2 unsharpened rules, and 1 missing replication path; the remaining 33 have multiple exclusions or audit quarantines. The one replication-path case, `tariff_protection_duration_growth_drag`, is a bounded review candidate, not a counted conversion. The eight missing-verdict cases require source/result/replay and correction review before any reconciliation. Estimator failures and non-results require new runs or designs; a metadata edit cannot certify them.

The 1,320 legacy same-commit records all require a new prospective specification and result for strict public status. The frozen 9 October queue selected 500 for **review**, with zero new registrations, runs, or graduations at queue creation. In the selected 500, only 51 have no review flags; 356 require full design review, 335 lack old evidence packets, 147 are screening/proxy designs, 124 lack manifests, 104 are heritage cross-sectional direct-measure reviews, and 10 have missing variables. Flags overlap, and an unflagged old case still needs a new first registration, source lock, exact result, and strict gate check.

## Distinctness and source coverage

The 500 selected queue records declare 335 different treatment/outcome **source signatures**; 213 records belong to signatures used by at least two cases. Across all 1,320 legacy records there are 797 such signatures and 612 records in repeated-signature groups. Signature counts are only a coarse screening bound: identical sources can support genuinely different periods or estimands, while different source strings can still describe aliases. Neither 335 nor 797 is a forecast of graduations.

The local pinned corpus is broad (1,926 Parquet vintages across 86 source directories, including 456 WDI files), but file presence and country/year keys do not establish measured values, suitable treatment timing, claim match, or estimator validity. A frozen protected-land/food family on separate source branch `3a80230af987dac4175653719302dab830d50735` illustrates the gap: 172 key-eligible economies became 0 complete because the pinned protected-area file had no 2005 measurements and the food-index file had no 2023 measurements. Both outcomes were honestly INCONCLUSIVE and added zero public cases. In contrast, the direct female-participation and agricultural-transition forward cases on this branch each passed their sample gates but yielded PARTIAL descriptive evidence, one public case each and no causal or policy/school credit. These hand-selected examples do not estimate the success rate of the whole queue.

## Feasibility judgment

The pinned corpus supports a **substantial research queue**, including direct-measure replacements for old proxies. It does **not** yet establish a sizable graduation-ready batch that can close the 291-record gap under unchanged gates. The defensible present conversion count from the remaining queue is zero until individual designs are registered before selected-value access, source-locked, run, replayed, and audited. Prioritize the one replication-path case and the eight missing-verdict reviews for bounded repair; then rank prospective families by direct claim match, source coverage at fixed years, independent outcome meaning, and first-registration feasibility. Count each outcome only after its own frozen floors pass. Do not use an old positive verdict, repeated source signature, post-result window change, or missingness-driven replacement as graduation evidence.

### Reproduction of the audit counts

Generate a temporary preregistration index with `scripts/check_preregistration.py --write-index --index <TEMP_INDEX>`, set `audit_evidence_tiers.PREREG_INDEX` to that temporary file, and call `audit_evidence_tiers.build()`. The review-flag and source-signature counts come from `engine/audits/prospective_v2_500_review_queue_2026-10-09.json` and the referenced hypothesis specifications. No generated preregistration, evidence, census, or web indexes were modified or committed for this audit.
