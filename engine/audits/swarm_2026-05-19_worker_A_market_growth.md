# Worker A market-friendly growth lane audit - 2026-05-19

## Scope

Worker A claimed the incomplete artifacts from `engine/queue_market_friendly_100.yaml` ranks 1-10:

- Rank 1: `firm_entry_rate_long_run_productivity`
- Rank 2: `pension_forced_saving_capital_deepening`
- Rank 8: `politicised_credit_election_cycle_growth_drag`
- Rank 9: `chile_market_reform_long_horizon_with_democracy`
- Rank 10: `canada_market_liberalisation_vs_state_industry_1988_2024`

Ranks 3-7 already had complete core artifacts and were left unchanged.

## Results

| hypothesis_id | verdict | packet data quality | artifact status |
| --- | --- | --- | --- |
| `firm_entry_rate_long_run_productivity` | SUPPORTED | incomplete | `diagnostics.json`, `result_card.md`, `replication.py`, `manifest.yaml`, and `evidence_packet.yaml` present |
| `pension_forced_saving_capital_deepening` | PARTIAL | incomplete | `diagnostics.json`, `result_card.md`, `replication.py`, `manifest.yaml`, and `evidence_packet.yaml` present |
| `politicised_credit_election_cycle_growth_drag` | PARTIAL | incomplete | `diagnostics.json`, `result_card.md`, `replication.py`, `manifest.yaml`, and `evidence_packet.yaml` present |
| `chile_market_reform_long_horizon_with_democracy` | PARTIAL | reproducible_hash_verified | `diagnostics.json`, `result_card.md`, `replication.py`, `manifest.yaml`, and `evidence_packet.yaml` present |
| `canada_market_liberalisation_vs_state_industry_1988_2024` | PARTIAL | reproducible_hash_verified | `diagnostics.json`, `result_card.md`, `replication.py`, `manifest.yaml`, and `evidence_packet.yaml` present |

## Blockers and caveats

- `firm_entry_rate_long_run_productivity`: evidence packet is intentionally marked incomplete. Missing preregistered series are `world_bank_wdi:IC.BUS.DENS` for `business_density`, `world_bank_wdi:IC.BUS.DENS` for `firm_entry_rate_interaction_proxy`, and `pwt:rnna` for `capital_deepening_rate`.
- `pension_forced_saving_capital_deepening`: evidence packet is intentionally marked incomplete. Missing preregistered series are `pwt:rnna`, `oecd_pension_statistics:pension_fund_assets`, `ilo:social_security_contribution_rate`, `world_bank_wdi:GFDD.DM.02`, and `world_bank_wdi:SP.POP.65UP.TO.ZS`.
- `politicised_credit_election_cycle_growth_drag`: evidence packet is intentionally marked incomplete. Missing preregistered series are `world_bank_wdi:GFDD.DM.04`, `constructed:binary`, `world_bank_wdi:GFDD.DM.02`, and `constructed:terms_of_trade_index`.
- No proxy verdicts were forced; missing data remains visible in each manifest and evidence packet.
- Whole-corpus `scripts/validate_specs.py` still fails on pre-existing schema debt outside this lane: 488 errors across 5398 checked files plus 64 permitted forward-reference warnings. The scoped artifact check for these five claimed runs passed.

## Commands run

- `sed -n '1,180p' engine/queue_market_friendly_100.yaml`
- `rg --files engine | rg '(^engine/hypotheses/|^engine/runs/|^engine/audits/swarm_2026-05-19_worker_A_market_growth.md$)'`
- `rg --files | rg '(^hypotheses/|^engine/hypotheses/).*(firm_entry_rate_long_run_productivity|pension_forced_saving_capital_deepening|ordo_anti_cartel_post_war_germany_economic_miracle|corruption_state_allocation_growth_interaction|australia_hawke_keating_reform_long_run|infrastructure_gap_state_investment_high_return|resource_developmentalism_rent_seeking_trap|politicised_credit_election_cycle_growth_drag|chile_market_reform_long_horizon_with_democracy|canada_market_liberalisation_vs_state_industry_1988_2024)\.yaml$'`
- `python3 -m py_compile scripts/generate_evidence_packets.py scripts/run_panel_fe.py scripts/run_event_study.py scripts/run_synth_did.py`
- `python3 scripts/generate_evidence_packets.py --run firm_entry_rate_long_run_productivity --run pension_forced_saving_capital_deepening --run politicised_credit_election_cycle_growth_drag --run chile_market_reform_long_horizon_with_democracy --run canada_market_liberalisation_vs_state_industry_1988_2024 --no-index`
- `python3 scripts/run_panel_fe.py firm_entry_rate_long_run_productivity`
- `python3 scripts/run_panel_fe.py pension_forced_saving_capital_deepening`
- `python3 scripts/run_panel_fe.py canada_market_liberalisation_vs_state_industry_1988_2024`
- `python3 scripts/run_event_study.py politicised_credit_election_cycle_growth_drag`
- `python3 scripts/run_synth_did.py chile_market_reform_long_horizon_with_democracy`
- `python3 scripts/validate_specs.py`
- Scoped artifact check: loaded each claimed run's `diagnostics.json`, `manifest.yaml`, and `evidence_packet.yaml`, and verified the five required files exist.

## Notes

- The first attempt to call `scripts/run_panel_fe.py` with three hypothesis IDs in one invocation failed because that runner accepts only one positional `hypothesis_id`. It was rerun once per ID and all three skipped cleanly with committed verdicts already on disk.
- Existing dirty files in the explicit do-not-touch areas were observed and left untouched: `web/app/scoreboard/page.tsx`, `data/manifests/fetch_run_2026-05-17T231721Z.yaml`, `data/manifests/fetch_run_2026-05-17T231736Z.yaml`, and `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231721Z.*` / `engine/audits/daily_rate_limited_data_backfill_2026-05-17T231736Z.*`.
