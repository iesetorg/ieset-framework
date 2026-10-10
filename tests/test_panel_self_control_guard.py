"""A duplicated outcome/control must never produce a directional panel verdict."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_panel_fe import run_panel_ols, verdict_from_estimate


def test_exact_outcome_as_control_fails_before_estimation():
    rows = [
        {
            "country_iso3": country,
            "year": year,
            "outcome": float(year - 1990 + country_offset),
            "treatment": float((year - 1990) % 7 + country_offset),
        }
        for country, country_offset in (("AAA", 0), ("BBB", 3))
        for year in range(2000, 2020)
    ]
    panel = pd.DataFrame(rows)
    panel["same_outcome_control"] = panel["outcome"].copy()
    spec = {
        "variables": {"controls": [{"name": "same_outcome_control"}]},
        "estimator": {"fixed_effects": ["country", "year"], "clustering": "country"},
        "sample": {"countries": ["AAA", "BBB"], "temporal_structure": "panel"},
    }

    estimate = run_panel_ols(panel, spec, "outcome", "treatment")

    assert estimate["method_valid"] is False
    assert estimate["self_controls"] == ["same_outcome_control"]
    assert "identical to control" in estimate["error"]
    assert verdict_from_estimate(estimate, "+")[0] == "INCONCLUSIVE_DATA_PENDING"
