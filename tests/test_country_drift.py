"""The public drift chart includes the complete coded movement history."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compute_country_drift.py"
SPEC = importlib.util.spec_from_file_location("compute_country_drift", SCRIPT)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)


def test_earliest_movement_sets_first_year_and_opening_value():
    movements = [
        {
            "movement_id": "pre_window",
            "countries": ["AAA"],
            "_start": 1970,
            "_end": 1975,
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "moderate"}
            ],
        },
        {
            "movement_id": "in_window",
            "countries": ["AAA", "BBB"],
            "_start": 1980,
            "_end": 1980,
            "axes_summary": [
                {"axis": "regulatory.trade_openness", "direction": "+", "magnitude": "strong"}
            ],
        },
    ]

    out = DRIFT.build_drift(movements)

    assert out["year_min"] == 1970
    assert out["years"] == list(range(1970, 1981))
    assert out["countries"]["AAA"]["statist_drift"][0] == 2.0
    assert out["countries"]["AAA"]["statist_drift"][-1] == -1.0
    assert out["countries"]["BBB"]["statist_drift"][0] == 0.0
    assert out["countries"]["BBB"]["first_coded_year"] == 1980
    assert out["countries"]["BBB"]["statist_drift"][-1] == -3.0


def test_subnational_movement_does_not_change_country_line_or_labels():
    movements = [
        {
            "movement_id": "national_reform",
            "countries": ["USA"],
            "_start": 2005,
            "_end": 2005,
            "leaders": ["National leader"],
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "weak"}
            ],
        },
        {
            "movement_id": "state_reform",
            "scope": "subnational",
            "countries": ["USA"],
            "_start": 2006,
            "_end": 2006,
            "leaders": ["State governor"],
            "axes_summary": [
                {"axis": "fiscal.spending_level", "direction": "+", "magnitude": "strong"}
            ],
        },
    ]

    out = DRIFT.build_drift(movements)
    usa = out["countries"]["USA"]

    assert out["years"] == [2005]
    assert usa["statist_drift"] == [1.0]
    assert usa["movement_count"] == 1
    assert [movement["movement_id"] for movement in usa["movements"]] == ["national_reform"]


def test_context_only_movement_does_not_double_count_primary_episode():
    primary = {
        "movement_id": "broad_programme",
        "countries": ["USA"],
        "_start": 2017,
        "_end": 2021,
        "axes_summary": [
            {"axis": "fiscal.tax_corporate", "direction": "-", "magnitude": "strong"}
        ],
    }
    context = {
        "movement_id": "tax_law_detail",
        "country_drift_role": "context_only",
        "country_drift_primary_movement": "broad_programme",
        "countries": ["USA"],
        "_start": 2017,
        "_end": 2017,
        "axes_summary": primary["axes_summary"],
    }

    out = DRIFT.build_drift([primary, context])

    assert out["countries"]["USA"]["movement_count"] == 1
    assert out["countries"]["USA"]["axes"]["fiscal.tax_corporate"] == [-3.0]


def test_context_only_movement_requires_existing_primary():
    context = {
        "movement_id": "tax_law_detail",
        "country_drift_role": "context_only",
        "country_drift_primary_movement": "missing_primary",
        "countries": ["USA"],
        "_start": 2017,
        "_end": 2017,
    }

    with pytest.raises(ValueError, match="missing primary"):
        DRIFT.build_drift([context])


def test_military_mentions_do_not_mark_civilian_movements_authoritarian():
    civilian = {
        "doctrine": "Foreign military aid and civil-military reform under an elected government.",
        "axes_summary": [],
    }
    military_regime = {
        "doctrine": "A military transition governed through a military council.",
        "axes_summary": [],
    }

    assert DRIFT.classify_movement_tone(civilian) == "neutral"
    assert DRIFT.classify_movement_tone(military_regime) == "auth"


def test_direct_price_controls_contribute_to_the_composite():
    movement = {
        "movement_id": "direct_price_controls",
        "countries": ["AAA"],
        "_start": 1971,
        "_end": 1971,
        "axes_summary": [
            {"axis": "regulatory.price_control_intensity", "direction": "+", "magnitude": "strong"}
        ],
    }

    out = DRIFT.build_drift([movement])

    assert out["countries"]["AAA"]["statist_drift"] == [3.0]


def test_corpus_map_starts_with_its_earliest_coded_event():
    movements = DRIFT.load_movements()
    out = DRIFT.build_drift(movements)
    earliest_year = min(movement["_start"] for movement in movements)

    assert out["year_min"] == earliest_year
    assert out["years"][0] == earliest_year
    assert any(
        country["statist_drift"][0] != 0 for country in out["countries"].values()
    )


def test_reviewed_axis_year_moves_one_existing_step_without_double_counting():
    movement = {
        "movement_id": "multi_year_movement",
        "countries": ["AAA"],
        "_start": 2000,
        "_end": 2008,
        "axes_summary": [
            {
                "axis": "fiscal.transfer_expansion",
                "direction": "+",
                "magnitude": "weak",
                "rationale": "Period summary with a possible 2007 action",
            },
            {
                "axis": "fiscal.spending_level",
                "direction": "+",
                "magnitude": "moderate",
                "drift_attribution_year": 2005,
                "drift_attribution_basis": "Documented 2005 authorization, not a measured outcome",
            },
        ],
    }
    out = DRIFT.build_drift([movement])
    years = out["years"]
    trajectory = out["countries"]["AAA"]["statist_drift"]

    assert trajectory[years.index(2000)] == 1.0
    assert trajectory[years.index(2004)] == 1.0
    assert trajectory[years.index(2005)] == 3.0
    assert out["countries"]["AAA"]["explicit_axis_timing"][0]["attribution_year"] == 2005
    assert out["timing_summary"]["explicit_axis_year_entries"] == 1
    review = DRIFT.timing_review([movement])
    assert review["summary"]["unresolved_later_year_rationale_entries"] == 1
    assert review["review_queue"][0]["axis"] == "fiscal.transfer_expansion"


def test_reviewed_start_year_is_counted_as_explicit_timing():
    movement = {
        "movement_id": "dated_opening_law",
        "countries": ["AAA"],
        "_start": 1887,
        "_end": 1890,
        "axes_summary": [{
            "axis": "regulatory.product_market_competition",
            "direction": "mixed",
            "magnitude": "weak",
            "rationale": "1887 act with uncertain net competition effect",
            "drift_attribution_year": 1887,
            "drift_attribution_basis": "Act enacted in 1887",
        }],
    }
    out = DRIFT.build_drift([movement])
    assert out["timing_summary"]["explicit_axis_year_entries"] == 1
    assert out["timing_summary"]["movement_start_proxy_entries"] == 0
    assert out["countries"]["AAA"]["explicit_axis_timing"][0]["attribution_year"] == 1887


def test_corpus_timing_exceptions_are_explicit_and_ambiguous_entries_stay_queued():
    movements = {movement["movement_id"]: movement for movement in DRIFT.load_movements()}
    swiss = movements["switzerland_federal_council_ordoliberal_continuity_1992_present"]
    czech = movements["czech_republic_fiala_spolu_2021_2025"]
    swiss_transfer = next(entry for entry in swiss["axes_summary"] if entry["axis"] == "fiscal.transfer_expansion")
    czech_spending = next(entry for entry in czech["axes_summary"] if entry["axis"] == "fiscal.spending_level")

    assert DRIFT.axis_attribution_year(swiss, swiss_transfer) == 2026
    assert DRIFT.axis_attribution_year(czech, czech_spending) == 2024
    review = DRIFT.timing_review(list(movements.values()))
    assert any(
        row["movement_id"] == swiss["movement_id"]
        and row["axis"] == "fiscal.spending_level"
        for row in review["review_queue"]
    )
    assert any(
        row["movement_id"] == czech["movement_id"]
        and row["axis"] == "fiscal.tax_corporate"
        and row["manual_review_note"]
        for row in review["review_queue"]
    )
