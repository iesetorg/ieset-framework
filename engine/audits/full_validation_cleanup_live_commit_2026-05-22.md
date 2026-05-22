# Full Validation Cleanup Live Commit - 2026-05-22

## Purpose

Clean the repository so the full validation gate passes before publishing the
latest hypothesis waves and supporting artifacts.

## What Changed

- Repaired legacy hypothesis schema drift:
  - filled missing `falsification.test` identifiers;
  - converted empty sample-country placeholders into broad `GLOBAL` samples;
  - replaced `ALL` scope tokens with `GLOBAL`;
  - filled empty `scope.outcome_dim` values from topic/claim context;
  - converted `covers_claims: null` to empty arrays;
  - added missing steelman pointers and steelman markdown stubs;
  - added canonical-case checklist fields where pre-registered
    `canonical_case_multi_metric` hypotheses lacked them;
  - moved a legacy `estimator.event_year` field into estimator notes.
- Repaired position claim scope gaps by copying linked-hypothesis scope where
  possible and otherwise filling conservative broad scope metadata.
- Updated `schemas/hypothesis.schema.json` so `sample.countries` accepts the
  same broad group tokens already accepted by `scope.countries`.
- Published the recent 45-hypothesis run package:
  - 32 free-market / redistribution specs and run artifacts;
  - 13 data-hunt specs and run artifacts;
  - cleanup and run audit notes.
- Refreshed runnability, scope-alignment, and link-reciprocity audit outputs.

## Validation

- `python3 scripts/validate_specs.py`
  - OK: 5,443 spec files validated + cross-references clean.
  - Remaining output is permitted candidate forward-reference warnings.
- `python3 scripts/audit_runnability.py`
  - 1,657 total specs; 1,575 READY; 82 NEEDS_DATA; 0 NEEDS_TEMPLATE;
    0 LEGACY_SCHEMA; 1,657 HAS_RUN.
- `python3 scripts/validate_scope_alignment.py`
  - 2,517 pass; 0 errors; 7 warnings.
- `python3 scripts/validate_link_reciprocity.py --summary`
  - 2,524 position-side links; 2,524 hypothesis-side coverages;
    0 errors; 0 warnings.
- `git diff --check`
  - clean.
