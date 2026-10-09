"""Documented axis decisions may occur after a movement begins."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)


def test_later_decision_changes_the_axis_only_in_its_documented_year() -> None:
    movement = {
        "movement_id": "later_decision",
        "countries": ["SWE"],
        "_start": 1933,
        "_end": 1935,
        "axes_summary": [
            {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "weak"},
            {
                "axis": "fiscal.transfer_expansion",
                "direction": "+",
                "magnitude": "weak",
                "drift_attribution_year": 1934,
                "drift_attribution_basis": "1934 statute; benefit began in 1935",
            },
        ],
    }
    result = DRIFT.build_drift([movement])
    country = result["countries"]["SWE"]
    assert country["axis_first_year"]["fiscal.spending_level"] == 1933
    assert country["axis_first_year"]["fiscal.transfer_expansion"] == 1934
    assert country["axes"]["fiscal.transfer_expansion"] == [0.0, 1.0]
    assert country["statist_drift"] == [1.0, 2.0]


def test_attribution_year_requires_a_source_basis_and_within_period_date() -> None:
    movement = {
        "movement_id": "bad_timing",
        "countries": ["USA"],
        "_start": 1887,
        "_end": 1890,
        "axes_summary": [],
    }
    entry = {
        "axis": "regulatory.product_market_competition",
        "direction": "+",
        "drift_attribution_year": 1890,
    }
    with pytest.raises(ValueError, match="needs a basis"):
        DRIFT.axis_attribution_year(movement, entry)
    entry["drift_attribution_basis"] = "Statute approved in 1890"
    assert DRIFT.axis_attribution_year(movement, entry) == 1890
    entry["drift_attribution_year"] = 1891
    with pytest.raises(ValueError, match="outside movement"):
        DRIFT.axis_attribution_year(movement, entry)
