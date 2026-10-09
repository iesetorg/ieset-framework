"""Fail-closed vintage custody for exact repairs of archived v1 runs.

The earlier generic packets had no source manifest.  The checked-in lock lists
the exact files used for these repairs.  Every replay checks both their bytes
and the mutable latest-vintage resolution before loading a panel.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import yaml

import run_panel_fe

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "scripts" / "frozen_source_vintages.json"
FLOAT_TOKEN = re.compile(r"(?<![\w.])[-+]?(?:\d+\.\d*|\.\d+)(?:[eE][-+]?\d+)?")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def same_packet(actual, stored) -> bool:
    """Compare every field, allowing only floating-point replay roundoff."""
    if type(actual) is not type(stored):
        return False
    if isinstance(actual, dict):
        return actual.keys() == stored.keys() and all(
            same_packet(actual[key], stored[key]) for key in actual
        )
    if isinstance(actual, list):
        return len(actual) == len(stored) and all(
            same_packet(left, right) for left, right in zip(actual, stored)
        )
    if isinstance(actual, float):
        return math.isclose(actual, stored, rel_tol=1e-10, abs_tol=1e-12)
    return actual == stored


def same_result_card(actual: str, stored: str) -> bool:
    """Keep prose, labels, integers and hashes exact; tolerate float roundoff."""
    left, right = FLOAT_TOKEN.split(actual), FLOAT_TOKEN.split(stored)
    left_numbers = FLOAT_TOKEN.findall(actual)
    right_numbers = FLOAT_TOKEN.findall(stored)
    return (
        left == right
        and len(left_numbers) == len(right_numbers)
        and all(
            math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-12)
            for a, b in zip(left_numbers, right_numbers)
        )
    )


def source_rows(hypothesis_id: str) -> list[dict]:
    lock = json.loads(LOCK_PATH.read_text())
    if lock.get("schema_version") != 1:
        raise RuntimeError("frozen source-lock schema changed")
    rows = lock["cases"][hypothesis_id]
    keys = [(row["publisher"], row["series"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise RuntimeError("duplicate frozen source-lock key")
    for row in rows:
        path = ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"pinned source bytes changed or missing: {row['path']}")
        current = run_panel_fe.latest_vintage(row["publisher"], row["series"])
        if current is None or current.resolve() != path.resolve():
            raise RuntimeError(f"latest vintage drifted from pin: {row['publisher']}:{row['series']}")
    return rows


def pinned_vintage(hypothesis_id: str, publisher: str, series: str) -> Path:
    rows = source_rows(hypothesis_id)
    row = next((r for r in rows if (r["publisher"], r["series"]) == (publisher, series)), None)
    if row is None:
        raise RuntimeError(f"unregistered source in frozen replay: {publisher}:{series}")
    return ROOT / row["path"]


def checked_build_panel(hypothesis_id: str, spec: dict):
    """Load through the pinned latest resolver and reject any source drift."""
    rows = source_rows(hypothesis_id)
    pins = {(row["publisher"], row["series"]): row for row in rows}
    original = run_panel_fe.latest_vintage
    seen: set[tuple[str, str]] = set()

    def checked_latest(publisher: str, series: str):
        key = (publisher, series)
        if key not in pins:
            raise RuntimeError(f"unregistered source in frozen replay: {publisher}:{series}")
        seen.add(key)
        return ROOT / pins[key]["path"]

    run_panel_fe.latest_vintage = checked_latest
    try:
        result = run_panel_fe.build_panel(spec)
    finally:
        run_panel_fe.latest_vintage = original
    expected_panel_keys = set(pins) - ({("ucdp", "ged")} if hypothesis_id == "privatisation_transition_tfp_panel" else set())
    if seen != expected_panel_keys:
        raise RuntimeError(f"frozen source set changed: expected {sorted(expected_panel_keys)}, observed {sorted(seen)}")
    return result


def provenance(hypothesis_id: str) -> dict:
    return {
        "source_lock_path": str(LOCK_PATH.relative_to(ROOT)),
        "source_lock_sha256": sha256_file(LOCK_PATH),
        "source_vintages": source_rows(hypothesis_id),
    }


def manifest_text(diagnostics: dict) -> str:
    p = diagnostics["provenance"]
    manifest = {
        "schema_version": 1,
        "hypothesis_id": diagnostics["hypothesis_id"],
        "runner": diagnostics["runner"],
        "spec_path": p["spec_path"],
        "spec_sha256": p["spec_sha256"],
        "source_lock_path": p["source_lock_path"],
        "source_lock_sha256": p["source_lock_sha256"],
        "source_vintages": p["source_vintages"],
        "input_panel_sha256": p["input_panel_sha256"],
        "prior_run": p["prior_run"],
    }
    if "frozen_spec_inconsistency" in diagnostics:
        manifest["frozen_spec_inconsistency"] = diagnostics["frozen_spec_inconsistency"]
    return yaml.safe_dump(manifest, sort_keys=False)
