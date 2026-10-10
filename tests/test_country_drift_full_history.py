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
    assert result["countries"]["GBR"]["composite_first_year"] == 1846
    assert result["countries"]["CAN"]["composite_first_year"] == 1980
    # Raw zeroes remain aligned for replication, but the chart hides them
    # using the first-coded-year metadata.
    can = result["countries"]["CAN"]["statist_drift"]
    assert can[result["years"].index(1976)] == 0
    assert can[result["years"].index(1980)] == -1


def test_french_1804_1814_steps_extend_the_signed_axis_history() -> None:
    result = DRIFT.build_drift(DRIFT.load_movements())
    france = result["countries"]["FRA"]
    rule_of_law = france["axes"]["institutional.rule_of_law"]

    assert result["year_min"] == 1804
    assert france["axis_first_year"]["institutional.rule_of_law"] == 1804
    assert rule_of_law[result["years"].index(1804)] == 1.0
    assert rule_of_law[result["years"].index(1814)] == 2.0
    assert min(
        country["composite_first_year"]
        for country in result["countries"].values()
        if country["composite_first_year"] is not None
    ) == 1846
    # These early institutional steps are outside the composite's axis set.
    assert france["composite_first_year"] > 1846


def test_composite_coverage_waits_for_valenced_axis_coding() -> None:
    movements = [
        {
            "movement_id": "umbrella",
            "countries": ["AAA"],
            "_start": 2000,
            "_end": None,
            "axes_summary": [],
        },
        {
            "movement_id": "unvalenced",
            "countries": ["AAA"],
            "_start": 2002,
            "_end": None,
            "axes_summary": [
                {"axis": "regulatory.immigration_openness", "direction": "+", "magnitude": "weak"},
                {"axis": "fiscal.spending_level", "direction": "mixed", "magnitude": "weak"},
            ],
        },
        {
            "movement_id": "later",
            "countries": ["AAA"],
            "_start": 2010,
            "_end": None,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "weak"},
            ],
        },
        {
            "movement_id": "only_umbrella",
            "countries": ["BBB"],
            "_start": 2000,
            "_end": None,
            "axes_summary": [],
        },
    ]
    result = DRIFT.build_drift(movements)
    assert result["countries"]["AAA"]["composite_first_year"] == 2010
    assert result["countries"]["BBB"]["composite_first_year"] is None
    assert result["countries"]["AAA"]["axis_first_year"]["regulatory.immigration_openness"] == 2002
    assert result["countries"]["AAA"]["axis_first_year"]["fiscal.spending_level"] == 2010


def test_axis_coverage_ignores_neutral_steps_but_keeps_offsetting_signed_steps() -> None:
    movements = [
        {
            "movement_id": "neutral",
            "countries": ["AAA"],
            "_start": 1900,
            "_end": None,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "0", "magnitude": "weak"},
                {"axis": "regulatory.sectoral_licensing", "direction": "mixed", "magnitude": "weak"},
            ],
        },
        {
            "movement_id": "offsetting",
            "countries": ["AAA"],
            "_start": 1904,
            "_end": None,
            "axes_summary": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "weak"},
                {"axis": "regulatory.trade_openness", "direction": "-", "magnitude": "weak"},
            ],
        },
        {
            "movement_id": "signed",
            "countries": ["AAA"],
            "_start": 1905,
            "_end": None,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "weak"},
            ],
        },
    ]
    result = DRIFT.build_drift(movements)
    aaa = result["countries"]["AAA"]
    assert aaa["axis_first_year"] == {
        "fiscal.spending_level": 1905,
        "regulatory.trade_openness": 1904,
    }
    assert aaa["composite_first_year"] == 1904
    assert aaa["axes"]["regulatory.trade_openness"] == [0.0] * 6


def test_opposing_same_year_steps_still_establish_composite_coverage() -> None:
    movements = [
        {
            "movement_id": "offsetting",
            "countries": ["AAA"],
            "_start": 2010,
            "_end": None,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "weak"},
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "weak"},
            ],
        }
    ]
    result = DRIFT.build_drift(movements)
    assert result["countries"]["AAA"]["statist_drift"] == [0.0]
    assert result["countries"]["AAA"]["composite_first_year"] == 2010


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
