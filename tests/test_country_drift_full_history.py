"""The public drift timeline must retain the full authored movement range."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)


def test_trajectories_begin_at_earliest_authored_movement() -> None:
    movements = [
        {
            "movement_id": "early",
            "name": "Early shift",
            "countries": ["GBR"],
            "_start": 1846,
            "_end": 1850,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "moderate"}
            ],
        },
        {
            "movement_id": "late",
            "name": "Late shift",
            "countries": ["CAN"],
            "_start": 1980,
            "_end": None,
            "axes_summary": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "weak"}
            ],
        },
        {
            "movement_id": "latest",
            "name": "Latest shift",
            "countries": ["GBR"],
            "_start": 2026,
            "_end": None,
            "axes_summary": [
                {"axis": "regulatory.trade_openness", "direction": "-", "magnitude": "weak"}
            ],
        },
    ]

    result = DRIFT.build_drift(movements)
    assert (result["year_min"], result["year_max"]) == (1846, 2026)
    assert len(result["years"]) == 181
    assert result["countries"]["GBR"]["axis_first_year"] == {
        "fiscal.spending_level": 1846,
        "regulatory.trade_openness": 2026,
    }
    assert result["countries"]["CAN"]["axis_first_year"] == {
        "regulatory.trade_openness": 1980
    }
    assert result["countries"]["CAN"]["movements"][0]["year"] == 1980
    # Raw zeroes remain aligned for replication, but the chart hides them
    # using the first-coded-year metadata.
    can = result["countries"]["CAN"]["statist_drift"]
    assert can[result["years"].index(1976)] == 0
    assert can[result["years"].index(1980)] == -1


def test_subnational_movement_does_not_change_country_total_or_event_log() -> None:
    national = {
        "movement_id": "federal",
        "countries": ["USA"],
        "_start": 2006,
        "_end": None,
        "axes_summary": [
            {"axis": "regulatory.environmental_stringency", "direction": "+", "magnitude": "weak"}
        ],
    }
    state = {
        "movement_id": "california",
        "countries": ["USA"],
        "scope": "subnational",
        "_start": 2006,
        "_end": None,
        "axes_summary": [
            {"axis": "regulatory.environmental_stringency", "direction": "+", "magnitude": "strong"}
        ],
    }

    result = DRIFT.build_drift([national, state])
    usa = result["countries"]["USA"]
    assert usa["statist_drift"] == [1.0]
    assert usa["movement_count"] == 1
    assert [m["movement_id"] for m in usa["movements"]] == ["federal"]


def test_supranational_movement_does_not_change_national_series_or_coverage() -> None:
    national = {
        "movement_id": "national",
        "countries": ["GBR"],
        "_start": 1846,
        "_end": None,
        "axes_summary": [
            {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "weak"}
        ],
    }
    eu_wide = {
        "movement_id": "eu_wide",
        "scope": "supranational",
        "countries": ["GBR", "LUX"],
        "_start": 1840,
        "_end": None,
        "axes_summary": [
            {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "strong"}
        ],
    }

    result = DRIFT.build_drift([national, eu_wide])
    assert (result["year_min"], result["year_max"]) == (1846, 1846)
    assert list(result["countries"]) == ["GBR"]
    assert result["countries"]["GBR"]["statist_drift"] == [-1.0]
    assert result["countries"]["GBR"]["movement_count"] == 1
    assert [m["movement_id"] for m in result["countries"]["GBR"]["movements"]] == ["national"]


def test_single_market_is_not_classified_as_a_national_movement() -> None:
    single_market = next(
        m for m in DRIFT.load_movements()
        if m["movement_id"] == "eu_single_market_1993"
    )
    assert single_market["scope"] == "supranational"
    assert "eu_single_european_act_1986" in single_market["policies"]
