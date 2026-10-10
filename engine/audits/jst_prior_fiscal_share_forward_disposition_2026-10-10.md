# JST prior fiscal-share family: archival disposition

Date: 2026-10-10. Isolated branch `codex/ieset-jst-fiscal-forward-2026`, based on `483f5122920ee4b66a233eecd920d951162544fc`. This note is an explicit **zero-conversion** handoff. None of the eight recorded results is public evidence or eligible for school, position, policy, causal, or featured credit.

## Frozen sequence and measured results

Registration `337bde04a3e4cf86012d83a98a73e4b6ade68424` introduced all eight specifications, steelmans, source plan, and runner before selected outcome measurement. Eight separate metadata locks were committed, one per result, from `f45e773e83c4213a19307caed44848d3dafbf511` through `55d8f41c6bd70d3ac54ec35d8ae3f9dce2e41f42`. The measured result packet appeared in `9f9b28c59a7f2d31dc1fa7a6668faf0dc1b17042`. The exact JST R6 source is `data/vintages/jst/jst_r6@2026-04-30T114353Z.parquet`, SHA-256 `4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f`, locally fetched under `data/manifests/fetch_run_2026-04-30T105817Z.yaml`. Source bytes are ignored and not committed. JST R6 is licensed CC BY-NC-SA 4.0; a separate rights review remains necessary for any public use.

The fixed eight cells cover five-year forward real income, real consumption, investment-share, unemployment, CPI, short-rate, long-rate, and current-account-share responses. Every cell cleared its frozen sample, variance, influence, rank, and cluster-SE gates, with 281–312 complete country-anchors across all 18 countries and 18 anchors. Every recorded internal verdict is PARTIAL; the smallest Bonferroni-adjusted p-value is 0.06079, above the family cutoff of 0.01. No directional claim passed. The runner's read-only `verify` exactly reproduced all 48 result packet files after the result commit.

## Why every result remains archived

The original committed specification for each cell omitted `falsification.threshold.family_id`. The public evidence-tier gate requires that field in the **first committed specification** for a multi-outcome family, matching the diagnostic, lock, and packet family ID. A fresh preregistration index recognizes all eight registration/run pairs as `verified`, but direct `audit_evidence_tiers.build_record` evaluation returns `archive` and `verdict_missing` for all eight because its immutable nested-result gate declines the family. This is a registration-contract failure, not an absent measured estimate. The source plan, runner, locks, and packets carried the family ID; they cannot retroactively repair the first committed specification. The specification, gate, result bytes, and historical verdicts were left unchanged. No subsequent metadata edit may turn this first run into a public conversion.

The run selected the registered outcome years for modeling, but its Parquet reader loaded all outcome columns for the full file before filtering those years in memory. Therefore earlier pre-1900 values and null masks from this **same source file** have been accessed computationally and cannot be described as a blind new holdout. A new design would need genuinely fresh independent source evidence and a new ID, with the prior results disclosed.

## Handoff

Keep this branch as an inspectable archive of the attempted family. If merged into integration, count **eight additional archived records and zero public conversions**. Recompute the preregistration and evidence-tier indexes after integration, and retain the historical failure. No push, mainline merge, publication, or raw data transfer was performed by this lane.
