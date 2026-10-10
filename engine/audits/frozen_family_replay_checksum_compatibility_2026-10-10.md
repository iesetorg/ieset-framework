# Frozen-family replay checksum compatibility — 2026-10-10

The integrated GFDD banking-crisis and WDI resource-rent families retain their original preregistered runners, source locks, diagnostics, evidence packets, verdicts, and thresholds. Their runners' `verify` modes compare JSON/YAML numerical fields with a 1e-9 relative and 1e-11 absolute tolerance, but also compare a SHA-256 over *newly serialized* diagnostic floats. In this integrated checkout, both original modes passed the numeric comparison and then stopped at the first `evidence_packet.yaml.reproduction.result_sha256` comparison. No stored diagnostic was edited.

Separate companion verifiers now recompute the selected results with the immutable runners; compare all numerical fields under those runners' frozen tolerances; require each saved packet checksum to equal SHA-256 of its saved `diagnostics.json` bytes; compare the saved YAML fields semantically and the saved presentation files to the saved diagnostic result; and check the saved family report against those saved results. This avoids treating a tiny reserialization difference as corrupted evidence while preserving the checksum's original custody purpose.

| Family | Integrated replay | Recorded verdicts |
| --- | --- | --- |
| GFDD bank resilience / future crisis onset | `python3 scripts/verify_gfdd_bank_resilience_crisis_2026.py --source-root '<matching local raw cache>'` passed | 2 PARTIAL, 6 INCONCLUSIVE |
| WDI resource rents / later sector growth | `python3 scripts/verify_wdi_resource_rents_sector_growth_2026.py --source-root '<matching local raw cache>'` passed | 8 INCONCLUSIVE |

These are tolerance-based numerical replays with exact saved-byte checksum checks, **not byte-identical recomputations of floating-point diagnostics**. They do not turn any frozen failure into a public result or repair GFDD's missing original fetch manifest. The FAOSTAT eight-test family independently passed its original `--verify` exact replay in this checkout.
