# Worker B Institutional-Quality Queue Ranks 11-25

Date: 2026-05-19
Lane: Worker B, market-friendly institutional-quality queue ranks 11-25
Scope touched: only claimed run directories plus this audit file.

## Claimed IDs

| rank | hypothesis_id | verdict | estimate summary | packet quality |
| ---: | --- | --- | --- | --- |
| 13 | `procurement_competition_corruption` | SUPPORTED | coef +0.2050, p 0.0329, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 16 | `licensing_discretion_bribery` | SUPPORTED | coef +0.2050, p 0.0329, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 17 | `market_reform_civil_liberties_interaction` | PARTIAL | coef -0.0897, p 0.1960, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 18 | `market_freedom_democratic_resilience` | PARTIAL | coef -0.1081, p 0.3331, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 22 | `rule_bound_regulation_business_trust` | SUPPORTED | coef +0.2050, p 0.0329, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 24 | `frontier_qol_market_institutions_1990_2024` | SUPPORTED | coef +3077.7877, p 0.0042, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |
| 25 | `market_governance_qol_broad_scope` | SUPPORTED | coef +0.2050, p 0.0329, n 1000, countries 40 | reproducible_hash_verified, 4 inputs |

## Artifacts Produced

Each claimed run now has:

- `diagnostics.json`
- `result_card.md`
- `manifest.yaml`
- `evidence_packet.yaml`
- `replication.py`

The manifests were generated from the refreshed canonical `scripts/run_panel_fe.py` diagnostics and resolve exact vintage parquet files plus SHA-256 hashes. Evidence packets were generated with `--no-index` to avoid rewriting the global packet index from this lane.

## Commands Run

```bash
python3 engine/runs/procurement_competition_corruption/replication.py
python3 engine/runs/licensing_discretion_bribery/replication.py
python3 engine/runs/market_reform_civil_liberties_interaction/replication.py
python3 engine/runs/market_freedom_democratic_resilience/replication.py
python3 engine/runs/rule_bound_regulation_business_trust/replication.py
python3 engine/runs/frontier_qol_market_institutions_1990_2024/replication.py
python3 engine/runs/market_governance_qol_broad_scope/replication.py
python3 scripts/generate_evidence_packets.py --run procurement_competition_corruption --run licensing_discretion_bribery --run market_reform_civil_liberties_interaction --run market_freedom_democratic_resilience --run rule_bound_regulation_business_trust --run frontier_qol_market_institutions_1990_2024 --run market_governance_qol_broad_scope --no-index
python3 -m py_compile engine/runs/procurement_competition_corruption/replication.py engine/runs/licensing_discretion_bribery/replication.py engine/runs/market_reform_civil_liberties_interaction/replication.py engine/runs/market_freedom_democratic_resilience/replication.py engine/runs/rule_bound_regulation_business_trust/replication.py engine/runs/frontier_qol_market_institutions_1990_2024/replication.py engine/runs/market_governance_qol_broad_scope/replication.py
python3 scripts/validate_specs.py
```

Additional targeted checks:

- Confirmed all 7 claimed run directories contain diagnostics, result card, manifest, evidence packet, and replication wrapper.
- Confirmed all 7 evidence packets have `reproducible_hash_verified` provenance with 4 inputs and zero missing artifacts.
- Targeted hypothesis-schema validation passed for all 7 claimed hypothesis YAMLs.

## Repairs

Two run-local wrappers had stale imports and failed from repo root:

- `engine/runs/rule_bound_regulation_business_trust/replication.py`
- `engine/runs/market_governance_qol_broad_scope/replication.py`

Both were repaired to add the repo `scripts/` directory to `sys.path`, matching the other canonical panel wrappers. No shared runner code was changed.

## Blockers And Caveats

- Full `python3 scripts/validate_specs.py` still fails on 488 unrelated pre-existing corpus/schema errors across non-claimed hypotheses, positions, and publisher metadata. The selected seven hypothesis YAMLs pass targeted schema validation.
- Five supported IDs share the same broad WGI regulatory-quality to WGI control-of-corruption fingerprint (`coef +0.2050`, `p 0.0329`). Treat these as clean run artifacts, not independent scoreboard evidence until duplicate/proxy review decides whether to consolidate or upgrade them.
- The two partial democracy/resilience screens are non-decisive and should stay out of scoreboard conversion absent a stronger direct design.
- Arrow emitted sandbox `sysctlbyname` warnings while reading parquet files. The wrappers exited successfully and all packets are hash verified.
