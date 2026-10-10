"""Blind-access and frozen-estimator checks for the WASH child mortality family."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "wash_child", ROOT / "scripts/run_wash_child_mortality_2026.py")
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_key_only_mortality_projection_has_no_value_or_status(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.extend(columns)
        return pd.DataFrame([{"country_iso3": "GBR", "indicator_id": "SH.DYN.MORT",
                              "year": 2004}])

    monkeypatch.setattr(module.pd, "read_parquet", fake_read)
    assert module.mortality_keys(ROOT) == {("GBR", 2004)}
    assert "value" not in seen and "obs_status" not in seen


def _synthetic_panel(beta: float) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(7124)
    rows = []
    for index in range(110):
        country = f"C{index:03d}"
        country_effect = rng.normal(0, .005)
        for anchor in module.ANCHORS:
            x = rng.normal(0, .06) if anchor == 2004 else rng.normal(2, 1.5)
            prior_service = rng.uniform(20, 80)
            baseline = rng.uniform(1, 5)
            prior_change = rng.normal(-.1, .05)
            income = rng.normal(9, .7)
            income_change = rng.normal(.1, .04)
            y = (beta * x + .001 * prior_change + .001 * baseline
                 + country_effect + rng.normal(0, .003))
            rows.append({"country_iso3": country, "anchor": anchor, "x": x,
                         "prior_service_share": prior_service,
                         "log_baseline_mortality": baseline,
                         "prior_log_mortality_change": prior_change,
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
    panel, gate = _synthetic_panel(-.01)
    assert module.estimate("water", panel, gate)["verdict"] == "SUPPORTED"
    panel, gate = _synthetic_panel(+.01)
    assert module.estimate("water", panel, gate)["verdict"] == "REFUTED"


def test_failed_complete_case_gate_cannot_publish_a_slope():
    panel, gate = _synthetic_panel(-.01)
    gate["valid_rows"] = module.CASES["water"]["min_rows"] - 1
    result = module.estimate("water", panel, gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
