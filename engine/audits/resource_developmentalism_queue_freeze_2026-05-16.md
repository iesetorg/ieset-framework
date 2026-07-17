# Resource Developmentalism Hardening Queue Freeze - 2026-05-16

Target hypothesis: `resource_developmentalism_rent_seeking_trap`

Plan anchor: `internal research notes`

## Freeze State

This wave begins from a dirty worktree. Existing relevant dirty files include:

- `.gitignore`
- `hypotheses/growth/resource_developmentalism_rent_seeking_trap.yaml`
- `engine/runs/resource_developmentalism_rent_seeking_trap/diagnostics.json`
- `engine/runs/resource_developmentalism_rent_seeking_trap/result_card.md`
- `scripts/run_panel_fe.py`
- `scripts/build_export_diversification_vintage.py`
- `scripts/build_movement_vintages.py`
- `internal research notes`
- `engine/audits/corpus_dataset_review_2026-05-16.md`

The current swarm is an audit and fast-pass design wave. No worker may edit movement YAML, hypothesis YAML, shared runner code, scoreboard mappings, or existing run artifacts unless explicitly reassigned in a later implementation wave.

## Write Ownership

| Lane | Owner | Write scope |
| --- | --- | --- |
| Artifact reconciliation | Worker A | `engine/audits/resource_developmentalism_artifact_reconciliation_2026-05-16.md` |
| Data measurement | Worker B | `engine/audits/resource_developmentalism_data_measurement_plan_2026-05-16.md` |
| Treatment coding | Worker C | `engine/audits/resource_developmentalism_treatment_inventory_2026-05-16.csv`, `engine/audits/resource_developmentalism_treatment_audit_2026-05-16.md` |
| Outcome fast pass | Worker D | `engine/audits/resource_developmentalism_fast_pass_2026-05-16.md`, optional `.json` companion |
| Historical cases | Worker E | `engine/audits/resource_developmentalism_case_map_2026-05-16.md` |
| Estimator design | Worker F | `engine/audits/resource_developmentalism_estimator_redesign_2026-05-16.md` |
| QA synthesis | Main agent after worker return | `engine/audits/resource_developmentalism_swarm_synthesis_2026-05-16.md` |

## Stop Rules

- Stop if a worker needs to modify files outside its write scope.
- Stop if another process changes target run artifacts during the wave.
- Stop if a worker finds that the current treatment inventory is too noisy to support modeling without recoding.
- Stop before scoreboard changes.

## First Pass Goal

Produce enough evidence to decide whether to:

1. build a bespoke multi-outcome replication now,
2. repair treatment/data first, or
3. classify the current result as research-only until product-level trade data and subtype-aware treatment coding land.
