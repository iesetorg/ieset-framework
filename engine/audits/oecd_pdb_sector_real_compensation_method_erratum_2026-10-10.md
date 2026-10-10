# OECD PDB real-compensation family — post-measurement method-label erratum

The registered runner was executed after registration `bfe1c4cd1e40c44a76ae2ed668844e9f69e90435` and source locks `8742b08171a9dfc2ed65c59c2d7aaf2eb5f648ad`, `f49309e93149417cd1b7833891868b804e639ab2`, and `e6e0801388167120c196d81984bcbc01db23b10c`. Its shared fixed-effects estimator generated the correct model and results, but copied a generic text label saying **“prior employment growth”** into `result.primary.method`. The fifth design column was actually prior **CPI-deflated sector labour compensation growth**, as frozen in the hypothesis specs and supplied by the family runner. No employment series entered this family.

The first measured output was **not committed**. Before the first result commit, `scripts/run_oecd_pdb_sector_real_compensation_2026_metadata_fix.py` checked every original packet byte-for-byte against the frozen runner, checked the original diagnostic and report hashes below, then replaced only that method label and the exact-replay command/runner identity in its regenerated packet. It did not alter sources, keys, complete cases, outcome or treatment values, design matrix, coefficients, standard errors, p-values, Holm adjustment, fold results, gates, verdicts, or source locks. The wrapper and this erratum are added with the first measured-result commit; the preregistration remains byte-identical.

| Original uncommitted measured artifact | SHA-256 |
| --- | --- |
| Manufacturing `diagnostics.json` | `0342e712eb5553ae1233f2e6b271217224044a630412fe69d2757955621f67b2` |
| Wholesale/retail `diagnostics.json` | `821457e2498f6c4f3eeb1ff0ed994de8eb3c4c7ee4bef3997b04fd25739018cf` |
| ICT `diagnostics.json` | `59e6c94f8282e4261a0c3478c35723a4cf232b175f8fbaeccb62df530a07c330` |
| Aggregate result audit | `974fb3b6d252219742f180f9ce89f70db08e0566644a938525a0841d70dfd035` |

The unchanged measured verdicts are PARTIAL for all three sectors. This repair is metadata-only and offers no upgraded evidence or score credit. Reproduce the committed packets with `python3 scripts/run_oecd_pdb_sector_real_compensation_2026_metadata_fix.py verify --source-root /path/to/IESET` using exact local source vintages.
