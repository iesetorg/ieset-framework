"""Blind preflight and replay-contract checks for the ten-case BIS/HSL family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_bis_dsr_oecd_hsl_extended_2026.py"
spec = importlib.util.spec_from_file_location("bis_dsr_oecd_hsl_extended", RUNNER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_preflight_uses_only_oecd_dimensions_and_keys(monkeypatch):
    original = pd.read_parquet

    def guarded(path, *args, **kwargs):
        cols = kwargs.get("columns")
        if Path(path).name == Path(module.HSL).name:
            assert cols is not None
            assert "value" not in cols and "Observation value" not in cols
            assert "OBS_STATUS" not in cols and "Observation status" not in cols
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", guarded)
    report = module.key_preflight()
    assert report["measured_outcome_values_read"] is False
    assert report["outcome_null_masks_read"] is False
    assert len(report["cases"]) == 10


def test_serialized_confidence_interval_replays(tmp_path):
    expected = [{"term": "dsr_change_pp", "confidence_interval": [0.1, 0.2], "coefficient": 0.15}]
    target = tmp_path / "coefficients.parquet"
    pd.DataFrame(expected).to_parquet(target, index=False)
    actual = pd.read_parquet(target).to_dict(orient="records")
    assert isinstance(actual[0]["confidence_interval"], np.ndarray)
    module.equal_close(actual, expected, "synthetic coefficients")
    with pytest.raises(AssertionError):
        module.equal_close(actual, [{**expected[0], "coefficient": 0.4}], "tampered coefficients")


def test_value_bounds_cover_distinct_units():
    assert module.finite_range(120, 100) is None
    assert module.finite_range(120, 500) == 120
    assert module.finite_range(float("nan"), 500) is None
