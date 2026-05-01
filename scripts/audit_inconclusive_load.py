#!/usr/bin/env python3
"""Summarise where INCONCLUSIVE runner load is coming from.

Scans ``engine/runs/*/diagnostics.json`` and prints:

- total inconclusive count
- breakdown by template/runner
- breakdown by coarse reason bucket
- top missing publishers
- top missing series

This is meant for triage after large bulk runs, so it avoids third-party
dependencies and works directly off persisted diagnostics.
"""
from __future__ import annotations

import glob
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNS_GLOB = str(ROOT / "engine" / "runs" / "*" / "diagnostics.json")
TOKEN_SPLIT_RE = re.compile(r"[+;]")


def verdict_text(doc: dict) -> str:
    return str(doc.get("verdict_label") or doc.get("verdict") or "").strip()


def is_inconclusive(doc: dict) -> bool:
    return verdict_text(doc).upper().startswith("INCONCLUSIVE")


def classify_reason(doc: dict) -> str:
    reason = str(doc.get("verdict_reason") or verdict_text(doc)).lower()
    status = doc.get("data_status") or {}
    missing = status.get("variables_missing") if isinstance(status, dict) else []
    has_missing = bool(missing)

    if "falsification rule not sharpened" in reason:
        return "stub_rule"
    if "no outcome or no treatment variable" in reason:
        return "spec_shape_missing_outcome_or_treatment"
    if "no outcome variable in spec" in reason or reason == "no outcome variable":
        return "spec_shape_missing_outcome"
    if "no countries in sample" in reason:
        return "spec_shape_no_countries"
    if "couldn't infer event_year" in reason or "couldn't infer pre/post cut year" in reason:
        return "spec_shape_missing_event_year"
    if "need >=" in reason:
        return "sample_too_small_for_template"
    if "no outcome variable loaded" in reason or "no treatment variable loaded" in reason:
        return "preflight_missing_loaded_variable"
    if "variables not loaded" in reason:
        return "preflight_missing_multiple_variables"
    if "data gap" in reason:
        return "explicit_data_gap"
    if "insufficient" in reason or "no valid horizons" in reason:
        return "estimation_insufficient_observations"
    if has_missing:
        return "missing_series_other"
    return "other_inconclusive"


def iter_missing_tokens(doc: dict):
    status = doc.get("data_status") or {}
    missing = status.get("variables_missing") if isinstance(status, dict) else []
    for entry in missing or []:
        source = str(entry.get("source") or "").strip()
        if not source:
            continue
        for token in TOKEN_SPLIT_RE.split(source):
            token = token.strip()
            if not token or ":" not in token:
                continue
            publisher, series = token.split(":", 1)
            publisher = publisher.strip().lower()
            series = series.strip()
            if publisher and series:
                yield publisher, series


def main() -> int:
    by_template = Counter()
    by_runner = Counter()
    by_reason = Counter()
    by_publisher = Counter()
    by_series = Counter()
    total_runs = 0
    total_inconclusive = 0

    for path in glob.glob(RUNS_GLOB):
        total_runs += 1
        doc = json.loads(Path(path).read_text())
        if not is_inconclusive(doc):
            continue
        total_inconclusive += 1
        by_template[str(doc.get("template") or "unknown")] += 1
        by_runner[str(doc.get("runner") or "unknown")] += 1
        by_reason[classify_reason(doc)] += 1
        for publisher, series in iter_missing_tokens(doc):
            by_publisher[publisher] += 1
            by_series[f"{publisher}:{series}"] += 1

    print(f"diagnostics scanned: {total_runs}")
    print(f"inconclusive runs:   {total_inconclusive}")
    print("")

    print("By template:")
    for key, value in by_template.most_common():
        print(f"  {key:28s} {value:4d}")
    print("")

    print("By reason bucket:")
    for key, value in by_reason.most_common():
        print(f"  {key:36s} {value:4d}")
    print("")

    print("Top missing publishers:")
    for key, value in by_publisher.most_common(15):
        print(f"  {key:28s} {value:4d}")
    print("")

    print("Top missing series:")
    for key, value in by_series.most_common(20):
        print(f"  {key:56s} {value:4d}")
    print("")

    print("By runner:")
    for key, value in by_runner.most_common():
        print(f"  {key:56s} {value:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
