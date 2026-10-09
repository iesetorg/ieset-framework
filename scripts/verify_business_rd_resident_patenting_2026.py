#!/usr/bin/env python3
"""Read-only exact replay of frozen business-R&D/resident-patenting test."""
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
RUNNER_PATH = ROOT / "scripts/run_business_rd_resident_patenting_2026.py"
loader = importlib.util.spec_from_file_location("frozen_business_rd_patenting", RUNNER_PATH)
if loader is None or loader.loader is None:
    raise RuntimeError("cannot load frozen study runner")
study = importlib.util.module_from_spec(loader)
loader.loader.exec_module(study)


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify", action="store_true", required=True)
    parser.parse_args()
    revision = study.registration_commit()
    study.validate_spec()
    study.check_sources()
    study.check_lock(revision)
    folder = ROOT / study.RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    gate, verdict, reason, estimate = study.estimate_one()
    expected = study.artifacts(revision, gate, verdict, reason, estimate, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart")
    equal_close(normalize(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records")),
                expected["rows"], "coefficients")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / study.SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError("stored text differs from frozen replay")
    print("verified exact frozen-model replay", study.HYPOTHESIS_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
