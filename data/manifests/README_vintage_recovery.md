# Recover one pinned vintage from another checkout

Raw `data/vintages/` files are Git-ignored. The committed fetch manifests hold
relative file paths and SHA-256 hashes, so a source file can be brought into a
worktree without changing its recorded vintage or fetching a newer release.

From the destination checkout:

```sh
python3 scripts/restore_pinned_vintage.py \
  --source-root /absolute/path/to/other/IESET/checkout \
  data/vintages/publisher/series@vintage.parquet
```

This default form checks the committed pin, source hash, destination path, and
Git ignore rule. It reports what would happen without writing. Add `--apply`
to copy that one file:

```sh
python3 scripts/restore_pinned_vintage.py \
  --source-root /absolute/path/to/other/IESET/checkout \
  --apply \
  data/vintages/publisher/series@vintage.parquet
```

The command accepts only safe relative paths under `data/vintages/`. It reads
pins from `HEAD` in `data/manifests/*.yaml` and
`scripts/frozen_source_vintages.json`, including `entries[].parquet_path`,
`source_vintage.path`, and frozen case `path` records. A missing or conflicting
pin fails closed. An existing file is left in place only when its hash matches;
different bytes are never overwritten. Symlinked path components are rejected.
Neither the vintage bytes nor the external checkout path are saved in Git.

The check establishes byte identity with the committed manifest. It does not
establish that a source is fit for a new hypothesis; methodology, units, time
coverage, and preregistration still need review before a result is promoted.
