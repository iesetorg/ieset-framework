# PCW100 minimum-wage bite screen: calibration rescope — 2026-10-09

## Decision

`pcw100_us_mw_bite_ratio_p10_wage` moves from the September quarantine to **public calibration only**. The registered `SUPPORTED` label applies to an associational state/year fixed-effects screen, not a causal minimum-wage effect. All 17 school mappings were attached after the result. They remain reciprocal, inspectable historical links, but are **untested for school outcomes and receive zero school score credit**. No featured or mechanism claim is granted.

This decision supersedes claim 10's literal mechanical-identity and quartile-overlap assertions in `ieset_adversarial_supported_claims_2026-07-31.md` and `ieset_adversarial_audit_remediation_2026-09-03.md`. Those records remain as dated audit history. It also supersedes the decision boundary in the read-only `pcw100_us_mw_bite_ratio_p10_wage_integrity_replay_2026-10-09.md`, which held quarantine until the gate was applied.

## Evidence reviewed

- Spec and steelman first entered Git in `71888c2c1`; the run first entered in descendant `258598d14`. The associational design, direction, two-sided p<0.10 rule, minimum data gates, and contrast threshold were fixed before the run. The 17 `covers_claims` mappings entered later in `a913dbf95`, so this result cannot score them prospectively.
- The two derived analysis panels match the run manifest SHA-256 pins. The independent replay executed the original runner into a temporary directory and matched its coefficient Parquet, chart data, replication script, pre-correction card, diagnostics, and manifest after excluding only later correction/links and the fresh run timestamp. The state spine's current tracked file differs from its June manifest; the exact old bytes remain recoverable at `f3508d602:data/derived/state_universe_admin1.parquet`. That difference does not affect the pinned analysis panels used in the replay.
- Analytic sample: 459 unique state-year rows, 51 jurisdictions, nine observed years: 2014–2018, 2020–2021, 2023–2024. The written sample window was 2006–2024; ten years in that window have no analytic row. Bottom/top quartiles contain 115 rows each and have no state-year overlap. Repeated state names across quartiles represent different years.
- Treatment is legal minimum wage / BLS median hourly wage; outcome is separately sourced BLS p10 hourly wage. No top-quartile p10 wage is exactly the legal floor; two are one cent above. Full-model R²=0.974915 includes state and year effects and cannot prove a literal identity.
- The original estimate is +0.5883855769, state-clustered SE 0.0860611951, two-sided p=8.0965928468e-12. The registered directional verdict survives exact replay. Same-year wage-distribution coupling, endogenous floor changes, and other state-time confounding remain; this is a descriptive association, not a causal effect.

## Applied credit boundary

The run's `correction.disposition` is `rescoped_descriptive`, and `correction.school_score_eligible` is explicitly `false`. The generated evidence ledger publishes `public_visible=true`, `tier=calibration`, `school_score_eligible=false`, and `scoreboard_weight_cap=0.0`. This is a visibility decision, not a new estimate or prospective school test.

The Python scoreboard, the claim-level second-order gate index, and the TypeScript scoreboard all read that eligibility separately from public visibility. For the 17 mappings they retain the link and public hypothesis verdict, but emit `untested` school outcomes, zero weighted scores, and no tested-count or support-rate contribution. The `/h` school chips show a neutral `unscored` state. Position-side `empirical_status` was corrected from `supported` to `untested` on precisely those 17 mappings, with historical notes explicitly superseded. Reciprocal links and school predictions remain intact.

The causal next step is a separately registered event design with an independent outcome window and prospective school mappings. No such v2 run is credited here.
