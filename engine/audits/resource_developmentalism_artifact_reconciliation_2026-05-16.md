# Resource Developmentalism Artifact Reconciliation - 2026-05-16

Target: `resource_developmentalism_rent_seeking_trap`

Scope: read-only reconciliation of current run artifacts in `engine/runs/resource_developmentalism_rent_seeking_trap/` plus relevant local data manifests. No hypothesis YAML, run artifact, script, scoreboard, movement, or git-state changes were made.

## Summary

The current `diagnostics.json` and `result_card.md` agree with each other: the latest run completed as `PARTIAL` at `2026-05-16T08:53:53+00:00`, with coefficient `-0.008094`, p-value `0.758`, `1,320` observations, and `73` countries.

The current `evidence_packet.yaml` is stale. It was generated at `2026-05-15T19:29:56+00:00` and still records the earlier `INCONCLUSIVE_DATA_PENDING` preflight state: no treatment variable loaded, no input vintages, and no data inputs. Its recorded hashes for `diagnostics.json` and `result_card.md` no longer match the current files.

The run directory has no `manifest.yaml` or equivalent run-local provenance manifest. The only files present are `diagnostics.json`, `result_card.md`, `evidence_packet.yaml`, and `replication.py`.

## Artifact Reconciliation

| Artifact | Current state | Reconciliation finding |
| --- | --- | --- |
| `diagnostics.json` | `PARTIAL`; coefficient `-0.008093771140413914`; p-value `0.7583533820960677`; `run_utc` `2026-05-16T08:53:53+00:00`; variables missing `[]` | Current and internally usable, but not backed by a run-local manifest. |
| `result_card.md` | Same verdict, estimate, variable list, row counts, and timestamp as diagnostics | Agrees with diagnostics; no stop-rule disagreement found. |
| `evidence_packet.yaml` | `INCONCLUSIVE_DATA_PENDING`; reason says missing `constructed:binary_coded_from_policy_description`; `data.inputs: []`; `input_count: 0`; caveat says no input vintages | Stale and should not be treated as describing the current run. It points to the previous preflight failure, not the successful panel run. |
| `replication.py` | Calls `run_one("resource_developmentalism_rent_seeking_trap", force=True, persist_preflight_inconclusive=True)` | Still present and minimal. It can rerun the generic panel, but does not pin vintages or produce a complete manifest. |
| Run manifest | Missing | Add a run-local manifest in the regeneration pass, or ensure the refreshed evidence packet embeds the equivalent provenance. |

Current file hashes:

- `diagnostics.json`: `645b4cb869858c2210beb9e8c740ef7a51ce990856aac698746b777ca5f65dea`, `2857` bytes
- `result_card.md`: `5c2f2f0199c2268f04d918c04fc1a6d6dfca92073157f08dbc4d4c4fbc22b6cc`, `1946` bytes
- `evidence_packet.yaml`: `dbb2e7daf98f83673557fa0adfab75b1c20bc497b053662304f5ba96163db07e`, `3380` bytes
- `replication.py`: `7f77545d6c68d9874214d09ac5723081ea9926599d6726b7e6ec165ed87eb6ea`, `455` bytes

## Current Input Vintages Resolved

These are the local vintages that the generic runner currently resolves for the spec's source tokens:

| Role | Source token | Resolved vintage | Relevant manifest |
| --- | --- | --- | --- |
| Outcome | `derived:export_diversification_index` | `data/vintages/derived/export_diversification_index@2026-05-16T085311Z.parquet` | `data/manifests/fetch_run_export_diversification_2026-05-16T085311Z.yaml` |
| Treatment | `movements:resource_developmentalism` | `data/vintages/movements/resource_developmentalism@2026-05-16T084233Z.parquet` | `data/manifests/fetch_run_movement_vintages_2026-05-16T084233Z.yaml` |
| Treatment/control | `world_bank_wdi:NY.GDP.TOTL.RT.ZS` | `data/vintages/world_bank_wdi/NY.GDP.TOTL.RT.ZS@2026-04-30T115056Z.parquet` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |
| Outcome loaded but not estimated | `pwt:rtfpna` | `data/vintages/pwt/rtfpna@2026-05-05T195242Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| Outcome loaded but not estimated | `world_bank_wdi:NV.IND.MANF.ZS` | `data/vintages/world_bank_wdi/NV.IND.MANF.ZS@2026-05-05T194954Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| Control | `maddison:mpd2020` | `data/vintages/maddison/mpd2020@2026-05-05T195302Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| Control | `wgi:RL.EST` | `data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |

Derived export-diversification components currently resolve to:

- `TX.VAL.AGRI.ZS.UN`: `data/vintages/world_bank_wdi/TX.VAL.AGRI.ZS.UN@2026-05-12T132702Z.parquet`
- `TX.VAL.FUEL.ZS.UN`: `data/vintages/world_bank_wdi/TX.VAL.FUEL.ZS.UN@2026-04-30T115204Z.parquet`
- `TX.VAL.MANF.ZS.UN`: `data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet`
- `TX.VAL.MMTL.ZS.UN`: `data/vintages/world_bank_wdi/TX.VAL.MMTL.ZS.UN@2026-04-30T131203Z.parquet`

The derived export manifest records the component series IDs and recipe, but it does not embed the exact component parquet paths or hashes. The ores/metals input `TX.VAL.MMTL.ZS.UN@2026-04-30T131203Z.parquet` was found on disk, but no dedicated fetch-run manifest entry was found for that exact vintage outside coverage/search records and the derived manifest's component list.

## Stale Or Risky Fields

- `evidence_packet.verdict.raw`, `bucket`, and `reason` are stale relative to diagnostics/result card.
- `evidence_packet.data.inputs`, `data_quality.input_count`, `official_source_count`, and `hash_status_counts` are stale because they still report no input vintages.
- `evidence_packet.artifacts` records old hashes for `diagnostics.json` and `result_card.md`.
- `evidence_packet.reproduction.runner` is `null`, while current diagnostics identify `scripts/run_panel_fe.py`.
- The evidence packet still references the old missing treatment token `constructed:binary_coded_from_policy_description`; the current hypothesis and diagnostics use `movements:resource_developmentalism`.
- The current run grades only the first loaded outcome, `export_diversification_index`; `total_factor_productivity_growth` and `manufacturing_va_share` are loaded but not estimated or reflected in the verdict.
- The current WGI control resolves to `wgi:RL.EST@2026-04-30T114245Z`, even though a newer `GOV_WGI_RL.EST@2026-05-05T195218Z` exists. This may be intended alias behavior, but the refreshed provenance should record the exact file used.

## Regeneration Checklist

1. Regenerate the evidence packet only after the hardened run exists, not from the current generic `PARTIAL` as a scoreboard-safe result.
2. Record the current verdict and estimate from diagnostics/result card, or mark the packet as superseded if a hardened run replaces them.
3. Embed all input vintage paths, hashes, row counts, date ranges, and manifests for derived export diversification, movement treatment, WDI resource rents, WDI manufacturing share, PWT TFP, Maddison, and WGI.
4. For `export_diversification_index`, record both the derived output vintage and the four underlying WDI component vintages with hashes.
5. Add or regenerate a run-local `manifest.yaml` equivalent that links the run timestamp, runner, hypothesis hash, input vintages, output artifact hashes, and model sample.
6. Make the evidence packet explicit that the current generic runner estimates only the first outcome and does not implement 30-year windows, market-open peer subtype coding, early public-investment channels, or multi-outcome grading.
7. Preserve the current stale packet as an audit trail until a refreshed packet is intentionally written by the appropriate implementation lane.

## Top Findings

1. Current diagnostics and result card are consistent, but the evidence packet is stale and describes the prior failed preflight.
2. The run has no local manifest, so provenance currently depends on reverse-resolving latest vintages rather than a pinned run record.
3. All primary input vintage paths resolve, but the derived diversification provenance needs deeper component pinning, especially for `TX.VAL.MMTL.ZS.UN`.
4. The current `PARTIAL` remains research-only: it is a contemporaneous single-outcome generic panel, not the preregistered 30-year, multi-outcome resource-peer design.
