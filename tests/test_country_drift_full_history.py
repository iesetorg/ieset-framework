"""The public drift timeline must retain the full authored movement range."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

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


def test_french_1789_1804_1814_steps_extend_the_signed_axis_history() -> None:
    result = DRIFT.build_drift(DRIFT.load_movements())
    france = result["countries"]["FRA"]
    rule_of_law = france["axes"]["institutional.rule_of_law"]

    assert result["year_min"] == 1789
    assert france["axis_first_year"]["institutional.rule_of_law"] == 1789
    assert rule_of_law[result["years"].index(1789)] == 1.0
    assert rule_of_law[result["years"].index(1804)] == 2.0
    assert rule_of_law[result["years"].index(1814)] == 3.0
    assert min(
        country["composite_first_year"]
        for country in result["countries"].values()
        if country["composite_first_year"] is not None
    ) == 1846
    # These early institutional steps are outside the composite's axis set.
    assert france["composite_first_year"] > 1846


def test_hawke_and_laar_steps_are_dated_and_country_specific() -> None:
    movements = DRIFT.load_movements()
    added = {
        "australia_hawke_alp_reform_1983_1991",
        "estonia_laar_market_tax_reform_1994_1995",
    }
    baseline = DRIFT.build_drift(
        [m for m in movements if m["movement_id"] not in added]
    )
    repaired = DRIFT.build_drift(movements)
    assert repaired["year_min"] == baseline["year_min"] == 1789
    changed = [
        iso3 for iso3 in repaired["countries"]
        if repaired["countries"][iso3] != baseline["countries"][iso3]
    ]
    assert changed == ["AUS", "EST"]

    aus = repaired["countries"]["AUS"]
    est = repaired["countries"]["EST"]
    assert aus["axis_first_year"]["regulatory.financial_deregulation"] == 1983
    year_1983 = repaired["years"].index(1983)
    year_1988 = repaired["years"].index(1988)
    assert aus["axes"]["regulatory.financial_deregulation"][year_1983] == -3.0
    assert (
        aus["axes"]["regulatory.trade_openness"][year_1988]
        - baseline["countries"]["AUS"]["axes"]["regulatory.trade_openness"][year_1988]
    ) == 3.0
    assert est["axis_first_year"]["fiscal.tax_progressivity"] == 1994
    assert est["axes"]["fiscal.tax_progressivity"][repaired["years"].index(1994)] == -3.0

    tax = yaml.safe_load((ROOT / "policies" / "estonia_flat_tax_1994.yaml").read_text())
    assert tax["timeframe"]["enacted_date"] == "1993-12-08"
    assert tax["timeframe"]["effective_date"] == "1994-01-01"
    assert tax["enacted_by"] == ["estonia_laar_market_tax_reform_1994_1995"]
    for policy_id in (
        "australia_hawke_keating_reforms_1983_1996",
        "au_hawke_keating_reform_package_1983_1996",
    ):
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        financial = [
            a for a in policy["axes_moved"]
            if a["axis"] == "regulatory.financial_deregulation"
        ]
        assert [a["direction"] for a in financial] == ["-"]
        assert "australia_hawke_alp_reform_1983_1991" in policy["enacted_by"]


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
