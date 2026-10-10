# Post-lock WBES CSV decoding erratum

The eight-cell WBES registration (`cb4dee498b6235984f91030421bf999dda824306`) and source locks ending at
`590ea184f640149b7ec54e61d73cd9aca9287354` preceded any fitted value access. The exact November 2024 World
Bank aggregate CSV has a small number of malformed UTF-8 bytes in text labels.
The registered runner used `encoding="utf-8-sig"` without an error policy, so
the unchanged runner would stop while scanning the pinned file.

This separately committed adapter uses `errors="replace"` **only** when the
frozen runner opens that exact CSV name as UTF-8 text. It does not alter the
file, its SHA-256, the registration, source locks, selected rows, model, sample
rules, quality gates, or verdict thresholds. A source-level scan confirmed all
1,764 selected rows' `cabr`, `year`, `cut`, `subcut`, `indicator`, `method`,
`sector_MS`, `value`, and `N` fields contain only ASCII bytes. The replacement
therefore affects unrelated text labels, not selected keys or measurements.

The adapter writes its own replay command and erratum reference into each
packet; `replication.py` invokes the adapter. Exact replay must be run through
`scripts/run_wbes_constraints_next_wave_encoding_adapter_2026.py --verify`
with the matching ignored raw-source root. The adapter was committed before
the first measured `--run`, retaining a clean post-lock chronology.
