#!/usr/bin/env python3
"""Pre-value source-key adapter for WDI aggregate rows with empty ISO3 IDs.

The frozen estimator remains unchanged. This adapter filters only source rows
whose country_iso3 is empty before duplicate-key validation. Such rows cannot
match any of the 512 fixed ISO3 roster keys. It also binds its exact bytes to
each source lock and names this adapter in replication artifacts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_doing_business_insolvency_followup_2026 as frozen  # noqa: E402

ADAPTER = "scripts/run_doing_business_insolvency_followup_2026_key_adapter.py"
_source_lock = frozen.source_lock
_artifact_bytes = frozen.artifact_bytes


def _key(row: dict) -> tuple[str, int] | None:
    country = row["country_iso3"]
    if country is None or not str(country).strip():
        return None
    return str(country).strip(), int(row["year"])


def parquet_keys(path: Path) -> set[tuple[str, int]]:
    rows = pq.read_table(path, columns=["country_iso3", "year"]).to_pylist()
    keys = [_key(row) for row in rows]
    kept = [key for key in keys if key is not None]
    if len(kept) != len(set(kept)):
        raise ValueError(f"duplicate nonempty country/year key in {path.name}")
    return set(kept)


def parquet_values(path: Path) -> dict[tuple[str, int], object]:
    rows = pq.read_table(path, columns=["country_iso3", "year", "value"]).to_pylist()
    values: dict[tuple[str, int], object] = {}
    for row in rows:
        key = _key(row)
        if key is None:
            continue
        if key in values:
            raise ValueError(f"duplicate nonempty country/year value key in {path.name}")
        values[key] = row["value"]
    return values


def source_lock(hid: str, reg_commit: str, body: bytes) -> dict:
    lock = _source_lock(hid, reg_commit, body)
    lock["source_key_adapter"] = {"path": ADAPTER,
                                  "sha256": frozen.file_sha(ROOT / ADAPTER)}
    return lock


def artifact_bytes(*args, **kwargs) -> dict[str, bytes]:
    old_runner = frozen.RUNNER
    frozen.RUNNER = ADAPTER
    try:
        return _artifact_bytes(*args, **kwargs)
    finally:
        frozen.RUNNER = old_runner


frozen.parquet_keys = parquet_keys
frozen.parquet_values = parquet_values
frozen.source_lock = source_lock
frozen.artifact_bytes = artifact_bytes


if __name__ == "__main__":
    raise SystemExit(frozen.main())
