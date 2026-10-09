#!/usr/bin/env python3
"""Read-only exact replay of the frozen cross-domain measured family."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/run_cross_domain_measured_followups_2026.py"
loader = importlib.util.spec_from_file_location("frozen_cross_domain_family", RUNNER_PATH)
if loader is None or loader.loader is None:
    raise RuntimeError("cannot load frozen family runner")
family = importlib.util.module_from_spec(loader)
loader.loader.exec_module(family)


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if hasattr(value, "tolist"):
        return normalize(value.tolist())
    return value


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: mismatch")


def check_one(hypothesis_id: str, revision: str) -> None:
    spec_rel, _, run_rel = family.paths(hypothesis_id)
    folder = ROOT / run_rel
    saved = json.loads((folder / "diagnostics.json").read_text())
    gate, verdict, reason, estimate = family.estimate_one(hypothesis_id)
    expected = family.artifacts(hypothesis_id, revision, gate, verdict, reason,
                                estimate, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], f"{hypothesis_id}.diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()),
                expected["manifest"], f"{hypothesis_id}.manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()),
                expected["packet"], f"{hypothesis_id}.packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()),
                expected["chart"], f"{hypothesis_id}.chart")
    equal_close(normalize(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records")),
                expected["rows"], f"{hypothesis_id}.coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError(f"{hypothesis_id}: stored text differs from frozen replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", nargs="?", const="all", required=True,
                        choices=[*family.TESTS, "all"])
    args = parser.parse_args()
    revision = family.registration_commit()
    family.validate_specs()
    family.check_sources()
    family.check_lock(revision)
    selected = family.TESTS if args.verify == "all" else [args.verify]
    for hypothesis_id in selected:
        check_one(hypothesis_id, revision)
        print("verified exact frozen-model replay", hypothesis_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
