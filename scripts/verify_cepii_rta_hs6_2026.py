#!/usr/bin/env python3
"""Replay the frozen CEPII/WITS study with a Parquet list-cell adapter.

The preregistered runner, estimator, source checks, and stored result packet
remain unchanged. Pandas restores a Parquet confidence-interval list cell as
a NumPy array; this adapter normalizes that cell only during comparison.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_cepii_rta_hs6_2026.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("frozen_cepii_rta_hs6", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen CEPII/WITS runner")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    original_equal_close = runner.equal_close

    def compare_with_parquet_list_adapter(actual: Any, expected: Any, label: str) -> None:
        if isinstance(expected, list) and isinstance(actual, np.ndarray):
            actual = actual.tolist()
        original_equal_close(actual, expected, label)

    runner.equal_close = compare_with_parquet_list_adapter
    runner.check_sources()
    revision = runner.registration_commit()
    preflight = runner.key_preflight()
    runner.check_source_lock(revision, preflight)
    rows = runner.load_roster()
    result = runner.estimate(rows, preflight)
    runner.verify_artifacts(revision, result)
    print("verified exact CEPII/WITS replay with Parquet CI-list adapter:",
          runner.HYPOTHESIS_ID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
