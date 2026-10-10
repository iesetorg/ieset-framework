"""Blindness and synthetic verdict checks for the 20-cell GDP/LFS family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_wdi_oecd_lfs_age_sex_2026.py"
spec = importlib.util.spec_from_file_location("wdi_oecd_lfs_age_sex", RUNNER)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_key_preflight_never_loads_selected_employment_values_or_statuses(monkeypatch):
    original = pd.read_parquet

    def guarded(path, *args, **kwargs):
        if Path(path).name == Path(module.LFS).name:
            cols = kwargs.get("columns")
            assert cols is not None
            assert not set(cols).intersection({"value", "Observation value", "OBS_STATUS", "Observation status"})
        return original(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_parquet", guarded)
    report = module.key_preflight()
    assert report["outcome_values_read"] is False
    assert report["outcome_null_masks_read"] is False
    assert report["outcome_statuses_read"] is False
    assert report["cases"] == 20
    assert report["shared_key_rows_per_case"] == 1094


def test_synthetic_direction_and_inconclusive_floor():
    growth = module.exposure_values()
    rows = module.load_roster()
    panel = pd.DataFrame([{"country_iso3": c, "year": y,
                           "gdp_growth": growth[c, y], "lagged_growth": growth[c, y - 1]}
                          for c, y in rows])
    rng = np.random.default_rng(20261010)
    noise = rng.normal(0, 0.1, len(panel))
    material = panel.gdp_growth.abs().ge(module.MATERIAL_X)
    base_gate = {"valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
                 "distinct_years": panel.year.nunique(),
                 "material_growth_rows": int(material.sum()),
                 "material_growth_countries": panel.loc[material, "country_iso3"].nunique()}
    for direction, expected in ((1, "SUPPORTED"), (-1, "REFUTED")):
        data = panel.copy()
        data["employment_change"] = direction * 0.5 * data.gdp_growth + noise
        result = module.estimate(data, base_gate.copy())
        assert result["verdict"] == expected
        assert result["primary"] is not None
        assert result["primary"]["p_value_two_sided"] <= module.P_MAX
    short = panel.head(20).copy()
    short["employment_change"] = 0.5 * short.gdp_growth
    gate = {"valid_rows": 20, "valid_countries": short.country_iso3.nunique(),
            "distinct_years": short.year.nunique(), "material_growth_rows": 20,
            "material_growth_countries": short.country_iso3.nunique()}
    assert module.estimate(short, gate)["verdict"] == "INCONCLUSIVE"
