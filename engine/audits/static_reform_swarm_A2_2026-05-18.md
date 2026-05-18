# Static Reform Swarm A2 Audit - 2026-05-18

Worker: A
Scope: static-treatment conversions, migration, broad reform episodes. No
scoreboard or position files were edited. Known/concurrent dirty fetch manifests,
daily-rate-limited backfill audits, and other-worker run artifacts were left
untouched.

## Artifacts Produced

| Hypothesis | Action | Verdict |
| --- | --- | --- |
| `demo_canada_points_system_immigration` | Replaced absorbed country-FE wrapper with exact local OECD migration bridge, plus manifest/result card/diagnostics. | WEAKENED - local tertiary-employment bridge premium is +0.15pp, below the +5pp refutation screen; direct DIOC attainment share and identified coefficient are still missing. |
| `demo_australia_high_skill_migration` | Added exact local OECD migration bridge wrapper, plus manifest/result card/diagnostics. | PARTIAL - latest AUS foreign-born/native employment gap is +0.17pp, but the available 2015-2023 mean is -2.86pp and the skill-stream series is missing. |
| `china_soe_vs_cee_privatised_growth` | Replaced absorbed China-dummy FE wrapper with aggregate industry-growth bridge, plus manifest/result card/diagnostics. | PARTIAL - China real industry value-added growth exceeds CEE/post-Soviet peer median by +6.72pp/yr, but industry-share and SOE ownership gates are not identified. |
| `oecd_product_market_deregulation_tfp_panel` | A2 produced an exact data-gap wrapper, but the run directory was superseded by a concurrent Worker D exact/proxy productivity artifact before final status; I did not overwrite the newer files. | Current file verdict is PARTIAL - short-window PMR decline proxy does not clear both positive/significant productivity gates. The A2 blocker still applies to the registered 1998-2019 PMR-reduction design. |
| `australia_hawke_keating_reform_long_run` | Added provenance manifest for the existing real `PARTIAL` verdict and regenerated only its evidence packet with `--no-index`. | PARTIAL - existing panel-FE estimate remains coef=-0.01702, p=0.55. Evidence packet now has 8 hash-verified inputs. |

Shared exact-run logic lives in
`engine/runs/static_reform_worker_a_exact.py`.

## Blockers And Caveats

- Canada: local OECD IMD measures employment rates by education and birthplace,
  not the direct foreign-born tertiary-attainment share requested by the claim.
  The exact bridge weakens the claim but is not a full DIOC refutation.
- Australia migration: the local OECD slice starts in 2015 for Australia, not
  2000, and no local skill-stream-share panel is available.
- China vs CEE: local WDI aggregate industry data cannot isolate strategic-sector
  SOEs or ownership form. A real ownership-form test needs sector-level output by
  ownership and a time-varying privatisation/enterprise-restructuring treatment.
- OECD PMR: older PMR waves are not local. A concurrent Worker D artifact uses a
  2018/2023 PMR-decline proxy and 2019-2024 PDB outcomes; that is useful, but it
  is a post-registered short-window proxy rather than the original 1998-2019
  panel design.

## Verification

```sh
PYTHONPYCACHEPREFIX=/private/tmp/pycache python3 -m py_compile engine/runs/static_reform_worker_a_exact.py engine/runs/demo_canada_points_system_immigration/replication.py engine/runs/demo_australia_high_skill_migration/replication.py engine/runs/china_soe_vs_cee_privatised_growth/replication.py engine/runs/oecd_product_market_deregulation_tfp_panel/replication.py
python3 engine/runs/demo_canada_points_system_immigration/replication.py
python3 engine/runs/demo_australia_high_skill_migration/replication.py
python3 engine/runs/china_soe_vs_cee_privatised_growth/replication.py
python3 engine/runs/oecd_product_market_deregulation_tfp_panel/replication.py  # A2 data-gap run, later superseded by concurrent Worker D artifact
python3 scripts/generate_evidence_packets.py --run australia_hawke_keating_reform_long_run --no-index
PYTHONPYCACHEPREFIX=/private/tmp/pycache python3 -m py_compile engine/runs/static_reform_worker_a_exact.py engine/runs/demo_canada_points_system_immigration/replication.py engine/runs/demo_australia_high_skill_migration/replication.py engine/runs/china_soe_vs_cee_privatised_growth/replication.py engine/runs/oecd_product_market_deregulation_tfp_panel/replication.py engine/runs/australia_hawke_keating_reform_long_run/replication.py
python3 -c "..."  # parsed five manifests and checked every recorded vintage SHA-256
```

The four exact wrapper runs emitted harmless Arrow `sysctlbyname` warnings in the
macOS sandbox, then exited 0. A later plain `py_compile` attempted to write
bytecode under `~/Library/Caches`; final compile verification used
`PYTHONPYCACHEPREFIX=/private/tmp/pycache` and passed.

## Churn And Restore Notes

- No scoreboard, position, `data/manifests/fetch_run_2026-05-17T2317*.yaml`,
  or `engine/audits/daily_rate_limited_data_backfill_2026-05-17T2317*` files
  were edited.
- No Worker A2 generic-rerun churn needs restore. The only rewritten result
  artifacts retained as A2 output are the three intentional exact conversions,
  the Hawke-Keating manifest/evidence packet, and this audit.
- The current `oecd_product_market_deregulation_tfp_panel` files are newer
  concurrent Worker D output. I left them in place and removed the PMR id from
  the A2 helper dispatch map to avoid accidental overwrite.
- Additional dirty files outside this lane were present during final status,
  including energy/climate, financial-fragility, trade/resource, and productivity
  worker artifacts. They appear to be concurrent worker output and were not
  modified by this pass.
