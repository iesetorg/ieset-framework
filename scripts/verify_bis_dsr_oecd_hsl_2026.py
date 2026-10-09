#!/usr/bin/env python3
"""Exact replay for the frozen BIS DSR / OECD HSL four-test family.

This adapter only normalizes Arrow's list-column representation when comparing
coefficients.parquet. It does not alter preregistration, source lock, panels,
estimates, verdicts, or stored result files.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

import run_bis_dsr_oecd_hsl_2026 as frozen


def normalize_arrow_lists(value):
    if isinstance(value, np.ndarray):
        return [normalize_arrow_lists(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize_arrow_lists(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_arrow_lists(item) for item in value]
    return value


def main() -> int:
    narrow = frozen.check_sources()
    registration = frozen.registration_commit()
    preflight = frozen.key_preflight()
    lock_commit = frozen.check_source_lock(registration, narrow, preflight)
    panels = frozen.measured_panels(frozen.load_roster())
    results = {key: frozen.estimate(*panels[key], frozen.CASES[key]) for key in frozen.CASES}
    for key, case in frozen.CASES.items():
        folder = frozen.ROOT / frozen.run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        expected = frozen.artifact_payload(key, case, results[key], registration, lock_commit, saved["run_utc"])
        frozen.equal_close(saved, expected["diagnostics"], f"{key}.diagnostics")
        frozen.equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], f"{key}.manifest")
        frozen.equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], f"{key}.packet")
        frozen.equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], f"{key}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (frozen.ROOT / frozen.spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != expected["card"]
                or (folder / "replication.py").read_text() != expected["wrapper"]):
            raise AssertionError(f"{key}: stored text differs from frozen replay")
        coefficients = normalize_arrow_lists(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"))
        frozen.equal_close(coefficients, expected["coefficients"], f"{key}.coefficients")
    if (frozen.ROOT / frozen.SUMMARY).read_text() != frozen.summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from frozen replay")
    print("verified exact replay", frozen.FAMILY, {k: v["verdict"] for k, v in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
