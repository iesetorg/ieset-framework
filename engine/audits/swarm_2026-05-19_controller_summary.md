# Swarm Controller Summary - 2026-05-19

## Scope

Launched six parallel workers across market-growth, institutional-quality, Heritage graduation, and inconclusive-repair lanes. The target was a 30-40 item local throughput wave without forcing proxy evidence into scoreboard conversion.

Known unrelated loose files were not part of this wave and should remain excluded from staging:

- `web/app/scoreboard/page.tsx`
- `data/manifests/fetch_run_2026-05-17T231721Z.yaml`
- `data/manifests/fetch_run_2026-05-17T231736Z.yaml`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*`
- `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`

## Worker-Lane Result Tally

Accepted worker-lane artifacts: 40.

- Supported: 9
- Partial or weakened: 24
- Refuted: 2
- Inconclusive data-pending: 4
- Blocked: 1

Verdict-bearing artifacts: 35.

Blocker / still-inconclusive repairs: 5.

Data-quality summary from evidence packets:

- `reproducible_hash_verified`: 34
- `partial_provenance`: 1
- `incomplete`: 3
- `no_input_vintages_recorded`: 2

## Additional Policy-Browser Provenance Work

Generated 40 additional evidence packets for already-tested, non-inconclusive runs that had manifests but no packet. These are verification/provenance upgrades, not new verdicts.

## Scoreboard Posture

Do not auto-map the full wave to the scoreboard.

- Heritage WGI/WDI panel variants are stronger than the original Heritage cross-section screens, but their manifests mark them as not scoreboard-eligible pending duplicate/design review.
- Several WGI institutional runs share a broad proxy fingerprint and need duplicate-weight review before score conversion.
- The three incomplete Worker A packets are usable as run artifacts, but should not be treated as dispositive until their missing preregistered series are resolved.
- The five blocker/inconclusive repairs are useful data-gap maps, not evidence wins.

## Validation

- 40 worker IDs have `diagnostics.json`, `result_card.md`, `manifest.yaml`, `evidence_packet.yaml`, and `replication.py`.
- Worker replication wrappers compile with `PYTHONPYCACHEPREFIX=/private/tmp/pycache`.
- Worker YAML/JSON artifacts parse.
- `git diff --check -- engine/runs engine/audits hypotheses`: clean.
- `python3 scripts/validate_scope_alignment.py`: 0 errors.
- `python3 scripts/validate_link_reciprocity.py --summary`: 0 errors, 0 warnings.
