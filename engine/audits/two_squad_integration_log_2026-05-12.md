# Two-Squad Integration Log - 2026-05-12

## Active Squads

### Group 1: Runnable Hypothesis Production

- A1 BIS credit-cycle batch.
- A2 OECD PDB productivity batch.
- A3 Eurostat energy-price batch.
- A4 SOCX/EPL/BLS welfare-labour-minimum-wage triage.

### Group 2: Conversion And Data Spine

- B1 scoreboard conversion queue.
- B2 OECD SDMX data spine.
- Local overflow: WITS/Comtrade data spine plan.
- Local overflow: reusable batch QA playbook.

## Acceptance Criteria

Any produced hypothesis batch must pass:

1. Every generated hypothesis has a steelman file.
2. Every run has diagnostics, manifest, result card, replication script.
3. Manifest verdict matches diagnostics verdict.
4. Country samples exclude aggregate pseudo-countries.
5. Outcome is not duplicated as a control.
6. Targeted schema scan has no matching errors.
7. Scope validation has 0 errors.
8. Any scoreboard conversion candidate has an explicit bucket and mapping requirement.

## Integration Order

1. Collect completed agent outputs.
2. Review changed paths, especially generated scripts.
3. Run targeted QA for each prefix.
4. Update tally by batch: attempted, supported, partial, refuted, inconclusive.
5. Add conversion candidates to the mapping queue only if they pass duplicate/broad-proxy checks.
6. Launch the two capped overflow agents if slots open and still useful.

## Local Overflow Completed

- `engine/audits/monthly_factory_batch_qa_playbook_2026-05-12.md`
- `engine/audits/wits_comtrade_data_spine_plan_2026-05-12.md`

## Completed Wave Integration

### Group 1 Verdict Tally

| Agent | Track | Promoted specs | Executed runs | Supported | Partial | Refuted / weak | Inconclusive / data pending |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | BIS credit-cycle | 10 | 10 | 1 | 6 | 1 | 2 |
| A2 | OECD PDB productivity | 8 | 8 | 5 | 0 | 3 | 0 |
| A3 | Eurostat energy-price | 10 | 8 | 1 | 7 | 0 | 2 |
| A4 | SOCX/EPL/BLS welfare-labour-minimum-wage | 10 | 10 | 2 | 2 | 6 | 0 |

Total promoted specs: 38.
Total executed/result-bearing runs: 36.
Run verdict tally: 9 supported, 15 partial, 10 refuted or weak, 2 inconclusive/data-pending.

### Group 2 Outputs

- B1 produced `engine/audits/scoreboard_conversion_queue_b1_2026-05-12.md`: usable as a staged 25-item conversion queue, not one uncapped scoreboard batch.
- B2 produced `scripts/discover_oecd_sdmx_support_2026_05_12.py` and `engine/audits/oecd_sdmx_spine_plan_agent_b2_2026-05-12.md`: usable as an offline OECD SDMX helper/plan.
- WITS/Comtrade plan was updated at `engine/audits/wits_comtrade_data_spine_plan_2026-05-12.md`: planning-only until publisher registration and smoke fetches exist.

### QA Results

- Repaired A2/A3/A4 generator schema issues and regenerated affected specs/runs.
- Removed stale invalid A4 SOCX specs from `hypotheses/welfare/` after replacement under `hypotheses/welfare_architecture/`.
- Targeted JSON-schema validation across today-facing BIS/OECD PDB/Eurostat/A4 specs checked 64 files with 0 errors.
- Artifact presence check for today-facing runs found no missing diagnostics, manifests, result cards, replication scripts, coefficients, or chart data.
- Manifest-verdict consistency check found 0 mismatches.
- `validate_scope_alignment.py` passed with 2313 pass, 0 errors, 6 warnings.

## Pending

- Stage scoreboard conversion from B1 in capped waves, respecting the max-per-school daily guardrail.
- Keep B2/WITS as data-spine plans until network smoke fetches and publisher registrations are added.
