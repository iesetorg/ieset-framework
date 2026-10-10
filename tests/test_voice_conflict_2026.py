"""Blind-access and frozen-estimator checks for the voice/conflict test."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "voice_conflict", ROOT / "scripts/run_voice_conflict_2026.py")
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_preflight_conflict_projection_has_no_count_columns(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.extend(columns)
        return pd.DataFrame([{"country_iso3": "GBR", "year": 2004}])

    monkeypatch.setattr(module.pd, "read_parquet", fake_read)
    assert module.conflict_keys(ROOT) == {("GBR", 2004)}
    assert all(column not in seen for column in module.CONFLICT_COLS)


def _synthetic_panel(direction: int) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(9314)
    rows = []
    for index in range(165):
        country = f"C{index:03d}"
        country_effect = rng.normal(0, .04)
        for anchor in module.ANCHORS:
            x = rng.normal(0, .02) if rng.uniform() < .3 else rng.normal(.1, .55)
            prior_conflict = int(rng.uniform() < .25)
            prior_count = np.log1p(rng.integers(1, 5)) if prior_conflict else 0
            probability = np.clip(.5 + direction * .45 * x + .06 * prior_conflict
                                  + country_effect, .03, .97)
            rows.append({"country_iso3": country, "anchor": anchor, "x": x,
                         "prior_voice_estimate": rng.normal(0, .6),
                         "prior_conflict_any": prior_conflict,
                         "prior_log_conflict_count": prior_count,
                         "log_income": rng.normal(9, .7),
                         "prior_log_income_change": rng.normal(.1, .04),
                         "y": int(rng.uniform() < probability)})
    panel = pd.DataFrame(rows)
    rise = panel.loc[panel.x.ge(module.MATERIAL_RISE), "country_iso3"]
    flat = panel.loc[panel.x.abs().le(module.FLAT_CHANGE), "country_iso3"]
    conflict = panel.loc[panel.y.eq(1), "country_iso3"]
    no_conflict = panel.loc[panel.y.eq(0), "country_iso3"]
    gate = {"valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
            "valid_anchors": panel.anchor.nunique(),
            "material_rise_rows": len(rise), "material_rise_countries": rise.nunique(),
            "flat_rows": len(flat), "flat_countries": flat.nunique(),
            "future_conflict_rows": len(conflict), "future_conflict_countries": conflict.nunique(),
            "future_no_conflict_rows": len(no_conflict),
            "future_no_conflict_countries": no_conflict.nunique()}
    return panel, gate


def test_negative_and_opposite_direction_are_distinct():
    panel, gate = _synthetic_panel(-1)
    assert module.estimate("voice", panel, gate)["verdict"] == "SUPPORTED"
    panel, gate = _synthetic_panel(+1)
    assert module.estimate("voice", panel, gate)["verdict"] == "REFUTED"


def test_failed_outcome_support_gate_withholds_estimate():
    panel, gate = _synthetic_panel(-1)
    gate["future_conflict_rows"] = module.MIN_CONFLICT_ROWS - 1
    result = module.estimate("voice", panel, gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
