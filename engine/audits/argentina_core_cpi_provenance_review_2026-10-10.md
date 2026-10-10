# Argentina core CPI holdout: retrospective provenance review

Date: 2026-10-10. This is an audit of an already observed result. It does not register a new test, restore a reverted run, or add a public graduation.

## Recorded sequence

1. Commit `ec22102a8e3bca7bb783ebcf1097b8457b7be7b3` first added the new-ID specification, steelman, runner, official source parquet, raw JSON, and 25-entry fetch manifest. The frozen primary was the twelve-month median of Argentina's core CPI month-on-month change in September 2025 through August 2026, plus the count of months at or below 3.0%.
2. Commit `580340397c2aa8df9612d488d6e6061501dd5322` ran that specification after the registration commit. Its saved verdict was `SUPPORTED`: median 2.2515965736314087%; 9 of 12 months at or below 3.0%. It claimed only single-country descriptive persistence and no policy, causal, or school-score credit.
3. Commits `d477a22cb99502b9018d003b1e45247f2db30ba9` and `5fcfdf106d73f1c31c359fb580b34fa826d34cfd` reverted the run and registration. The outcome and historical run are now known; no later same-endpoint registration can be blind.

## Source custody that can be disclosed safely

The original manifest's INDEC entry identifies [Argentina's official CPI series](https://apis.datos.gob.ar/series/api/series?ids=148.3_INIVELNAL_DICI_M_26,148.3_INUCLEONAL_DICI_M_19,148.3_IREGULANAL_DICI_M_22,148.3_IESTACINAL_DICI_M_25,147.3_IBIENESNAL_DICI_T_19,147.3_ISERVICNAL_DICI_T_22) and labels the core component `148.3_INUCLEONAL_DICI_M_19`. It records a fetch at `2026-10-09T12:16:09.688031+00:00`, monthly coverage from December 2016 to August 2026, and CC-BY 4.0 attribution to Argentina datos.gob.ar / INDEC. The relevant paths below are repository-relative.

| Artifact | SHA-256 |
| --- | --- |
| `data/vintages/indec_ipc/all@2026-10-09T121609Z.parquet` | `f093e71a89254c3c51d265bc45f1b4ef58e7e59a47113dd4e59416620b03bd98` |
| `data/raw/indec_ipc/all@2026-10-09T121609Z.json` | `5bc83847b0fe5f673ae0f7887b1337abdd1373eb183b757d439eb7216aa83c96` |
| Original full `data/manifests/fetch_run_2026-10-09T121824Z.yaml` | `befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960` |

Read-only verification against the local exact-hash parquet recomputed the twelve unrounded core rates from the 2025-08 baseline. It reproduced the saved median `2.251596573631408702460591250` and the 9/12 threshold count. The raw JSON and full manifest also matched their recorded hashes. This confirms arithmetic and local source custody; it does not make the result unseen again.

## Publication and graduation gate

The full pinned manifest contains 25 source entries. Two `raw_path` fields in unrelated Brazilian treasury entries contain local home paths. The INDEC entry itself has no local home path, but the runner locked the SHA-256 of the **whole** manifest and requires unchanged first-addition bytes. A source-only excerpt or redacted manifest would change that SHA and fail the registered runner. Restoring the original manifest would reintroduce local paths into the public tree. An amendment after the observed result could support a labelled **post hoc provenance replay** with exact source hashes and unchanged analytic thresholds, but must retain the redaction chronology and cannot claim an untouched original registration or a new blind result.

**Disposition:** keep this case excluded from the public graduation count under the current immutable-source gate. Preserve the historical `SUPPORTED` result as an audit fact only; do not replace the old `milei_reforms_reduce_argentine_inflation` verdict. Any future public inclusion needs an explicitly reviewed provenance-only amendment and replay standard, with a separate review of sensitive content already present in Git history. No push or merge follows from this audit.
