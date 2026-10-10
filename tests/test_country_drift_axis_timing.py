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


def test_progressive_era_steps_wait_for_cited_1906_1913_1914_laws() -> None:
    movement = next(
        m for m in DRIFT.load_movements()
        if m["movement_id"] == "us_progressive_era_reform_consensus_1901_1917"
    )
    assert {
        entry["axis"]: entry["drift_attribution_year"]
        for entry in movement["axes_summary"]
    } == {
        "regulatory.sectoral_licensing": 1906,
        "regulatory.product_market_competition": 1914,
        "regulatory.financial_deregulation": 1913,
        "monetary.central_bank_independence": 1913,
        "fiscal.tax_progressivity": 1913,
    }
    result = DRIFT.build_drift([movement])
    usa = result["countries"]["USA"]
    at = {year: index for index, year in enumerate(result["years"])}
    # Movement period starts in 1901, but its cited federal laws did not.
    for year in range(1901, 1906):
        assert usa["statist_drift"][at[year]] == 0.0
        assert all(series[at[year]] == 0.0 for series in usa["axes"].values())
    assert usa["statist_drift"][at[1906]] == 2.0
    assert usa["statist_drift"][at[1912]] == 2.0
    assert usa["statist_drift"][at[1913]] == 5.0
    assert usa["statist_drift"][at[1914]] == 3.0
