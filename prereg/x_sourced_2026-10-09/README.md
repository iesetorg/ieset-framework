# X-sourced hypotheses, 2026-10-09

11 draft specs drafted from high-engagement X claims (see `source_provenance.archive_refs` in each spec).

- `PREREG_LEDGER.json`: local freeze (SHA256 + UTC, 2026-10-09T12:21:22Z) written before any analysis ran.
  The spec files in `hypotheses/` are byte-identical to the ledger hashes (verify with `shasum -a 256`).
- The git commit adding these specs is the formal pre-registration point; results are committed in a later commit.
- Disclosure: headline values quoted in the source tweets were seen before drafting; thresholds were fixed before running.
- Schema comment line in each spec points at `../../../IESET/schemas/...` (build-dir path); left as-is to keep hashes intact.

## Results (added after the pre-registration commit)
- `runs/<hypothesis_id>/results.json` + `runs/summary.json`, produced by `scripts/run_x_hypotheses.py` (run 2026-10-09 ~12:22-12:27 UTC).
- `runs/_rerun_milei_reforms_reduce_argentine_inflation/`: rerun of the existing pre-registered card with a fresh INDEC vintage (output redirected; engine/runs untouched).
- `runs/factcheck_kobeissi_information_jobs_lowest_since_2014/`: descriptive fact-check, NOT pre-registered.
- `claims-ledger.csv`: 41 X claims mapped to cards/new specs with verdicts.
- Timing disclosure: the analyses ran after the local SHA256 freeze (12:21:22Z) but BEFORE the git pre-registration commit,
  so the git ordering is a formality here; the binding evidence of pre-commitment is the ledger hash match.
- Vintages are gitignored; provenance is in data/manifests/fetch_run_2026-10-09T12*.yaml / T1322*.yaml / T1323*.yaml.
