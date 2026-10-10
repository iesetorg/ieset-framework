"""Structural and estimator checks for the frozen urban WASH family."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "urban_wash", ROOT / "scripts/run_urbanization_urban_wash_2026.py")
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_key_only_who_projection_has_no_outcome_columns(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.extend(columns)
        return pd.DataFrame([{
            "country_iso3": "GBR", "year": 2004,
            "IndicatorCode": "WSH_WATER_SAFELY_MANAGED",
            "SpatialDimType": "COUNTRY", "Dim1Type": "RESIDENCEAREATYPE",
            "Dim1": "RESIDENCEAREATYPE_URB",
        }])

    monkeypatch.setattr(module.pd, "read_parquet", fake_read)
    assert module.who_keys(ROOT, "water") == {("GBR", 2004)}
    assert "value" not in seen and "NumericValue" not in seen and "Value" not in seen


def _synthetic_panel(beta: float) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(2718)
    rows = []
    for index in range(100):
        country = f"C{index:02d}"
        country_effect = rng.normal(0, .2)
        for anchor in module.ANCHORS:
            x = rng.normal(1, 1)
            prior_urban = rng.uniform(15, 80)
            baseline = rng.uniform(20, 80)
            prior_change = rng.normal(1, .5)
            income = rng.normal(9, .7)
            income_change = rng.normal(.1, .04)
            y = (beta * x + .08 * prior_change + .01 * baseline
                 + country_effect + rng.normal(0, .2))
            rows.append({"country_iso3": country, "anchor": anchor, "x": x,
                         "prior_urban_share": prior_urban,
                         "baseline_outcome": baseline,
                         "prior_outcome_change": prior_change,
                         "log_income": income,
                         "prior_log_income_change": income_change, "y": y})
    panel = pd.DataFrame(rows)
    rise = panel.loc[panel.x.ge(module.MATERIAL_RISE), "country_iso3"]
    flat = panel.loc[panel.x.abs().le(module.FLAT_CHANGE), "country_iso3"]
    gate = {"valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
            "valid_anchors": panel.anchor.nunique(),
            "material_rise_rows": len(rise), "material_rise_countries": rise.nunique(),
            "flat_rows": len(flat), "flat_countries": flat.nunique()}
    return panel, gate


def test_registered_direction_and_opposite_direction_are_distinct():
    panel, gate = _synthetic_panel(-.5)
    assert module.estimate("water", panel, gate)["verdict"] == "SUPPORTED"
    panel, gate = _synthetic_panel(+.5)
    assert module.estimate("water", panel, gate)["verdict"] == "REFUTED"


def test_failed_complete_case_gate_cannot_publish_a_slope():
    panel, gate = _synthetic_panel(-.5)
    gate["valid_rows"] = module.CASES["water"]["min_rows"] - 1
    result = module.estimate("water", panel, gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
