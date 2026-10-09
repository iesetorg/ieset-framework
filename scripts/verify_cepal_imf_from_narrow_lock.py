#!/usr/bin/env python3
"""Replay the frozen CEPAL/IMF result using its committed narrow source lock.

This post-result adapter changes source lookup only. The first-added runner,
specification, estimator, decision rule, and saved packet remain unchanged.
The broad fetch manifest's hash is pinned in both the spec and lock, but that
manifest is intentionally absent from this isolated checkout because its
unrelated entries contain local paths. This adapter verifies the three raw
bytes and the unchanged lock without claiming to re-audit those other entries.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_cepal_imf_inflation_next_year_national_poverty_panel.py"
runner_spec = importlib.util.spec_from_file_location("frozen_cepal_imf_runner", RUNNER_PATH)
assert runner_spec is not None and runner_spec.loader is not None
frozen = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(frozen)


def selected_entries_from_committed_lock() -> dict[str, dict[str, Any]]:
    lock = yaml.safe_load((ROOT / frozen.LOCK_REL).read_text(encoding="utf-8"))
    if not isinstance(lock, dict) or lock.get("schema_version") != 1 or lock.get("study_id") != frozen.HID:
        raise ValueError("invalid narrow CEPAL/IMF source lock")
    original = lock.get("original_tracked_manifest") or {}
    if (original.get("path") != frozen.SOURCE_MANIFEST
            or original.get("sha256") != frozen.SOURCE_MANIFEST_SHA256):
        raise ValueError("original broad-manifest identity differs from frozen registration")
    entries = lock.get("selected_source_entries")
    if not isinstance(entries, dict) or set(entries) != set(frozen.SOURCES):
        raise ValueError("narrow lock has missing or extra source roles")
    allowed = {
        "publisher", "series_id", "source_url", "methodology_url", "license",
        "fetch_utc", "rows", "frequency", "units", "currency", "start_date",
        "end_date", "sha256", "parquet_path",
    }
    for role, source in frozen.SOURCES.items():
        entry = entries[role]
        if (not isinstance(entry, dict) or set(entry) != allowed
                or entry.get("publisher") != source["publisher"]
                or entry.get("series_id") != source["series_id"]
                or entry.get("sha256") != source["sha256"]
                or entry.get("parquet_path") != source["path"]):
            raise ValueError(f"narrow source identity differs from frozen registration: {role}")
        if frozen.sha256(ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"raw source SHA mismatch: {role}")
    return entries


def verify() -> dict[str, Any]:
    # The frozen runner's own chronology and exact-packet checks still run.
    frozen.manifest_entries = selected_entries_from_committed_lock
    return frozen.check_one()


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
