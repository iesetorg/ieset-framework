# Worker F Inconclusive Repair - 2026-05-19

Scope: public-visibility / inconclusive repair lane. I used the
`public_visibility_repair_queue_2026-05-04.json`, registered runners, and
`engine/runnability.derived.yaml` to select runnable queue IDs not named in the
nearby Worker A-E audit files. I did not edit hypotheses, scoreboard files,
position files, data vintages, fetch manifests, or global evidence indexes.

## Results

| hypothesis_id | runner | verdict / blocker |
| --- | --- | --- |
| `tax_inequality_korea_progressive_turn_2017_2020` | `scripts/run_synth_did.py` | INCONCLUSIVE_DATA_PENDING - current OWID/WDI panel loads, but synth pre-period coverage still has only 10 years and 1 donor. |
| `industrial_policy_high_governance_success` | `scripts/run_panel_fe.py` | PARTIAL - coefficient +0.002981, p=0.209; direction is positive but not significant at alpha=0.10. |
| `rent_control_reduces_housing_supply_and_quality` | `engine/runs/.../replication.py` | BLOCKED - city/metro rent, permit, and listing outcomes are still absent; no country-level proxy was forced. |
| `price_controls_produce_shortages_and_quality_degradation` | `scripts/run_synth_did.py` | INCONCLUSIVE_DATA_PENDING - partial CPI/monetary/import data load, but core constructed price-ceiling/shortage/quality variables and donor coverage remain insufficient. |
| `tcja_2017_growth_effect` | `scripts/run_local_projections.py` | WEAKENED - GDP gate clears at 0.97pp and PNFI is -3.73% below pretrend; EMTR-elasticity gate is not loaded. |
| `colonial_institutions_post_independence_growth` | `scripts/run_panel_fe.py` | INCONCLUSIVE_DATA_PENDING - outcome/control panel loads, but the AJR settler-vs-extractive treatment remains missing. |
| `chile_post_1990_institutional_premium` | `scripts/run_multi_metric_checklist.py` | INCONCLUSIVE_DATA_PENDING - canonical checklist resolves 0 metrics with current local inputs. |

## Files Touched

- `engine/runs/tax_inequality_korea_progressive_turn_2017_2020/{diagnostics.json,result_card.md,replication.py,manifest.yaml,evidence_packet.yaml}`
- `engine/runs/industrial_policy_high_governance_success/{diagnostics.json,result_card.md,manifest.yaml,evidence_packet.yaml}`
- `engine/runs/rent_control_reduces_housing_supply_and_quality/{manifest.yaml,evidence_packet.yaml}`
- `engine/runs/price_controls_produce_shortages_and_quality_degradation/{diagnostics.json,result_card.md,replication.py,manifest.yaml,evidence_packet.yaml}`
- `engine/runs/tcja_2017_growth_effect/{diagnostics.json,result_card.md,manifest.yaml,evidence_packet.yaml}`
- `engine/runs/colonial_institutions_post_independence_growth/{diagnostics.json,result_card.md,replication.py,manifest.yaml,evidence_packet.yaml}`
- `engine/runs/chile_post_1990_institutional_premium/{diagnostics.json,manifest.yaml,replication.py,evidence_packet.yaml}`
- `engine/audits/swarm_2026-05-19_worker_F_inconclusive_repair.md`

## Commands

```sh
python3 scripts/run_synth_did.py tax_inequality_korea_progressive_turn_2017_2020 --force
python3 scripts/run_panel_fe.py industrial_policy_high_governance_success --force
python3 engine/runs/rent_control_reduces_housing_supply_and_quality/replication.py
python3 scripts/run_synth_did.py price_controls_produce_shortages_and_quality_degradation --force
python3 scripts/run_local_projections.py tcja_2017_growth_effect --force
python3 scripts/run_panel_fe.py colonial_institutions_post_independence_growth --force
python3 scripts/run_multi_metric_checklist.py chile_post_1990_institutional_premium --force
PYTHONPYCACHEPREFIX=/private/tmp/pycache python3 -m py_compile engine/runs/tax_inequality_korea_progressive_turn_2017_2020/replication.py engine/runs/price_controls_produce_shortages_and_quality_degradation/replication.py engine/runs/colonial_institutions_post_independence_growth/replication.py engine/runs/chile_post_1990_institutional_premium/replication.py engine/runs/industrial_policy_high_governance_success/replication.py engine/runs/tcja_2017_growth_effect/replication.py engine/runs/rent_control_reduces_housing_supply_and_quality/replication.py
python3 scripts/generate_evidence_packets.py --run tax_inequality_korea_progressive_turn_2017_2020 --run industrial_policy_high_governance_success --run rent_control_reduces_housing_supply_and_quality --run price_controls_produce_shortages_and_quality_degradation --run tcja_2017_growth_effect --run colonial_institutions_post_independence_growth --run chile_post_1990_institutional_premium --no-index
git diff --check -- engine/runs/tax_inequality_korea_progressive_turn_2017_2020 engine/runs/industrial_policy_high_governance_success engine/runs/rent_control_reduces_housing_supply_and_quality engine/runs/price_controls_produce_shortages_and_quality_degradation engine/runs/tcja_2017_growth_effect engine/runs/colonial_institutions_post_independence_growth engine/runs/chile_post_1990_institutional_premium
```

The parquet readers emitted sandbox Arrow CPU-info warnings (`sysctlbyname`
permission messages), but all runner commands exited 0. Evidence packets were
generated with `--no-index`; the global evidence packet index was not rewritten.
