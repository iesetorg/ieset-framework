# Live Commit Split Plan

Generated: 2026-05-13

## Current Dirty-Tree Snapshot

- Total entries: 894
- Modified/tracked entries: 444
- Untracked entries: 450

## Top-Level Load

| area | entries |
| --- | ---: |
| `engine` | 591 |
| `hypotheses` | 162 |
| `policies` | 60 |
| `data` | 36 |
| `movements` | 20 |
| `scripts` | 19 |
| `web` | 5 |
| `"Reply Guy` | 1 |

## Recommended Commit Waves

1. `data/fetchers` + related fetch manifests updates (source/connectivity changes).
2. `scripts/*2026_05_12.py` generator/promoter scripts as one tooling wave.
3. `hypotheses/*` + matching `hypotheses/steelman/*` by domain family (energy, labour, growth, etc.).
4. `engine/runs/*` artifacts by batch family (BIS, OECD-PDB, welfare-labour, eurostat-energy).
5. `policies/*` and `movements/*` content pack wave.
6. Regenerated indexes/audits (`engine/*index*.json|md`, `engine/audits/*.json|md`) after each wave.

## Safety Gates Per Wave

- `./venv/bin/python scripts/validate_scope_alignment.py --summary`
- `./venv/bin/python scripts/validate_link_reciprocity.py --summary`
- `git diff --check`
- refresh affected audit/index artifacts only for that wave

## Notes

- Keep claims-to-hypothesis reciprocity strict (0 errors, 0 warnings target).
- Keep labour legacy IDs canonicalized via script resolvers; avoid run-dir renames.
- Avoid mixing fetcher code with large run-artifact dumps in the same commit.
