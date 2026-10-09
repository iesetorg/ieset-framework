# Verified archive frozen-repair update — 2026-10-09

This supersedes the **headline counts and PCW100 status** in
`verified_archive_residual_audit_2026-10-09.md`. It is a read-only review of
the current source specifications, run packets, and evidence ledger. No
hypothesis, result, source vintage, verdict, tier, or school score was changed.

## Current ledger and finding

`python3 scripts/report_hypothesis_conversion_funnel.py --as-of 2026-10-09
--check` passed: **410 public visible / 1,944 hypotheses**, including **214
archived with verified registration**. The 410 comprise 51 featured and 359
calibration records. The verified archives have these *first-action* buckets;
simultaneous blockers remain in the funnel JSON.

| First action | Records |
| --- | ---: |
| Estimator repair and rerun | 155 |
| Data or design rerun | 46 |
| Integrity reconcile and rerun | 2 |
| Missing-result rerun | 8 |
| Prospective rule version required | 2 |
| Replication path review | 1 |

**No immediately runnable frozen-rule conversion was identified from the
current local corpus.** This is an audit finding, not a proof that every later
source backfill or method repair is impossible. A queue position, old
`SUPPORTED` label, or successful generic preflight cannot replace the complete
registered test. The 155 estimator cases include 131 near-zero GDP-per-capita /
Fraser proxy placeholders with an outcome also used as a control and an
unrelated test; they require genuinely prospective replacements. The remaining
24 estimator cases still fail the current estimator gate. The 46 data/design
non-results include 30 missing replication paths. Existing separate reviews
document the eight missing-result cases, tariff duration, Peru/Paraguay, and
the two still-quarantined integrity cases.

## Ranked source gates

1. `anglo_money_growth_public_crowding_stagnation_2019_2024` is the narrowest
   conditional old-ID lead. Its claim, sample, variables, estimator, and
   falsification blocks still match its first-addition registration, and it
   has a replay wrapper. Both local WDI `FM.LBL.BMNY.ZG` vintages have six
   Canada 2019–2024 rows but **zero non-null values**. A new source-custodied
   vintage of that *declared series*, complete for the required window,
   followed by a dedicated replay of the full four-country pattern rule is
   required before any verdict. The present generic six-metric checklist is
   insufficient to establish that rule. No alternate money measure or missing
   country substitution is licensed by the frozen specification.
2. `canada_gdp_pc_2024_2025_peer_holdout_v2` has a complete pre-result rule
   and runner, but its registered source is the **exact**
   `NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet` file at SHA-256
   `6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb`.
   A key/null-only inspection found all 14 registered country-year rows but
   **all seven 2025 values null**. The rule explicitly forbids a WDI vintage
   switch, imputation, peer substitution, or endpoint change. A future WDI
   release could motivate a new, disclosed registration; it cannot complete
   this frozen ID.

Four housing non-results with seemingly focused designs still lack registered
panels and exact contrasts: `catalonia_reference_rent_contract_supply_response_2020`
needs municipal designation/contract/listing data;
`france_reference_rents_paris_lille_phase_in` needs observed leases and the
Paris on/off/on city windows; `sf_rent_control_1994_small_multifamily_expansion`
needs historical building-class records; and
`stockholm_rent_queue_allocation_distortion` needs queue-stock and tenant
mobility measures. They are source and design work, not immediate conversions.
The 214-case verified archive is also an arithmetic ceiling below a target of
500 additional graduations; new prospective designs are necessary for a target
of that size.

## Evidence boundary

Only source keys and null masks were inspected for the two WDI gates above;
no new outcome magnitudes were read or fitted. The older residual audit's
`400 / 1,934` headline and PCW100 quarantine entry are stale. PCW100 now
appears in the current ledger as **descriptive calibration**, with school-score
eligibility false and weight cap zero; its promotion is included in the 410,
not in the 214 verified archives. Full case-specific source and method gates
remain in `hypothesis_conversion_funnel_2026-10-09.json`,
`archived_macro_frozen_repair_review_2026-10-09.md`,
`missing_result_eight_preflight_review_2026-10-09.md`, and
`five_case_integrity_recovery_review_2026-10-09.md`.
