# IESET advance-score capacity review — 2026-10-11

This review does not create or graduate a hypothesis. It counts claim rows separately from independent study IDs and does not change the school timing gate.

## Current gate and target

The timing manifest has 5,068 linked position claim rows including the benchmark control, of which 205 carry an exact reciprocal school prediction in the parent tree of their hypothesis's first run. It classifies 4,299 rows as linked to studies without strict spec-before-run registration and 564 as school links or reciprocal wording added or changed after the first run. Among the 16 ranked schools, 504 claim links reach public results; 488 also have a school-score-eligible verdict. Of those, 314 lack a pre-run reciprocal school forecast, leaving **174 scored advance claim rows from 56 distinct studies**. Only 64 claim rows from 21 distinct studies have a directional school outcome. Eight schools have no scored advance result. The gap to 200 directional rows per school is 3,136. An advance result requires a public, valid study outcome **and** a frozen school-specific forecast on both sides before its first run.

The timing gate explains the observed 488-to-174 drop on the same public corpus; 249 of the 314 removed score links are calibration-tier studies and 65 are featured-tier studies. Directional score links fell from 272 to 64. Git-parent inspection found no position claim for the linked study before its first run in 311 of the 314 cases; the other three concern one tobacco study whose claim scope changed after the run (one also changed polarity). Those changes cannot be treated as earlier forecasts by renaming a status or replaying the old result.

The existing 500-case prospective-v2 file is an ordered design-review queue with zero new registrations or graduations. It is not a run queue. Every old same-commit result was visible before selection, so a new ID, independent validation sample or revised estimand, result-blind source and rule lock, and a later run commit are required.

The corrected school equalization queue finds only **three** hidden claim links with a frozen pre-run school forecast. None can score now: the Brazil industrial-capability checklist needs its 2030 outcomes and canonical metrics; the Singapore CPF synthetic-control case lacks the declared treatment series, a viable donor design, and a sharpened rule; the Zimbabwe property-rights case lacks its monetary source, canonical metrics, replication, and a sharpened rule. Repairing other archived hypotheses without new pre-run school forecasts does not fill the advance-score gap.

## Registered but unrun pool

The registration index has 57 `registered_no_run` studies: 47 are publication-rights-held, three have reciprocal school links, and seven are public and unlinked. The linked three are a Social Democratic OECD Gini forecast first runnable after the 2032 release, a Degrowth material-footprint forecast first runnable after the 2034 release, and a newly frozen Degrowth EU material-accounting forecast awaiting its 2026 Eurostat endpoint. They add zero current score. The new forecast was committed before any first run; no outcome data was fetched for it.

Among the seven public unlinked cases, six Australian cases remain candidate packages: ATO small-firm survival, thin capitalisation investment, post-study graduate retention, 2026–2037 bracket-creep counterfactual, 2022–2026 budget-costing reconciliation, and post-2022 migration/rent pressure. Their specifications identify missing linked administrative microdata, publisher tables, or a required PBO counterfactual and have no executable first-run pipeline. They cannot acquire school score by adding links to a candidate.

The seventh, `us_state_minimum_wage_bite_teen_employment_2026`, has a frozen runner and roster but explicitly registers `school_score_eligible: false`, `school_score_credit: 0`, and `covers_claims: []`; the runner refuses any change to those fields. The direct official ACS Subject Table endpoint now requires a Census API key, and this original 51-state source lock is absent. A separately preregistered non-Alabama 400-key v2 already fit the same source/treatment family and returned `PARTIAL` (primary p=0.060767 versus 0.005). Alabama values were viewed before its source lock. Adding a school mapping to the original now would revise a frozen no-credit design while its outcome family is known. There is no honest immediate scoreboard result here.

## Executable first wave

The next runnable advance-score study must be a **new** school-native hypothesis. A research lead should first select an independent future release, unused outcome sample, or substantively revised estimand with direct source custody. The theory forecast, claim text, scope, polarity, family membership, thresholds, minimum sample, estimator, steelman, and both reciprocal links must be committed in one registration commit with no selected outcome values or run files. Preserve source URL, raw response, license, UTC fetch time, vintage manifest, and SHA before fitting. A later commit can hold the run and exact replay; then rebuild preregistration, timing, evidence-tier, claim-reciprocity, and school-coverage audits. Directional, null, mixed, and failed tests all remain in the record.

Near-term capacity from the seven already registered public unrun studies is **zero** qualifying school-score results. A future ACS teen-employment follow-up could be a research lead only after a distinct post-2024 outcome release and treatment vintage exist, and only under a new ID with a theory-specific claim and a disclosed earlier v2 result. As of this review, Census says the 2025 ACS one-year release date is being determined; 2024 Subject Table API data requests require a key. Do not schedule a result before the source exists.

## Scale check from the policy corpus

The refreshed event-treatment registry now covers all 3,653 policy records. Only nine state a treated/comparison structure; all nine still declare a missing direct outcome, microdata, timing, or measurement contract. The city panel has complete named local layers for two of 1,000 cities; the state panel has 53 of 54 named multi-layer records concentrated in one correlated US minimum-wage domain. These are source leads, not hundreds of independent ready experiments.

The earlier 100-test policy contrast wave demonstrates batch execution, but 69 of its verdicts were partial and only 17 passed its Benjamini–Hochberg q<0.10 screen. Its school forecasts were not frozen before the runs. Reusing that wave's results or linking its policies now does not add advance credit. Even if every new study later produces a directional result and every school has a defensible forecast for it, the eight zero-score schools mean at least 200 distinct new study IDs are required to reach 200 directional results per school. The research program must therefore register new outcome-blind families, acquire direct source data, run all registered tests, and retain null and contrary results.

The all-legacy v2 readiness audit examined 1,320 same-commit study IDs: 203 have fully pinned source paths and hashes, and only 22 of those have any confirmed additional raw calendar year in retained vintages. Those 22 overlap and still need a claim-matched independent design. Source custody and genuinely new observations, not archive relabeling, set the near-term ceiling.

## Sources in this checkout

- `engine/school_prediction_timing.json`
- `engine/preregistration_index.json`
- `engine/publication_rights_holds.json`
- `engine/policy_event_treatment_registry.json`
- `engine/policy_evidence_index.json`
- `engine/city_policy_test_readiness_summary.json`
- `engine/state_policy_test_readiness_summary.json`
- `engine/audits/school_coverage_balance_2026-10-11.md`
- `engine/audits/legacy_archive_v2_readiness_2026-10-10.md`
- `engine/audits/policy_contrast_wave_100_2026_07_18_graduation.json`
- `engine/audits/prospective_v2_500_review_queue_2026-10-09.md`
- `engine/audits/sparse_school_prospective_registration_2026-10-11.md`
- `hypotheses/labour/us_state_minimum_wage_bite_teen_employment_2026.yaml`
- `scripts/run_us_state_minimum_wage_bite_teen_employment_2026.py`
- `engine/audits/us_state_minimum_wage_bite_teen_employment_2026_source_access_2026-10-10.md`
- `engine/audits/us_state_minimum_wage_bite_teen_employment_non_alabama_2026_v2_result_2026-10-10.md`

Official source access: [ACS API example](https://api.census.gov/data/2024/acs/acs1/subject/examples.html) and [ACS updates](https://www.census.gov/programs-surveys/acs/news/updates.html).
