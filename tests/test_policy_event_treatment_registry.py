from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_policy_event_treatment_registry as registry  # noqa: E402


def test_timing_status_prefers_exact_event_dates():
    timeframe = {
        "start": 2021,
        "end": 2023,
        "enacted_date": "2021-11-11",
    }
    design = {
        "event_dates": [
            "2021-11-15 fuel cap effective",
            "2022-02 staple-food cap month",
            "2023 removal year",
        ],
    }

    assert registry.timing_status(timeframe, design) == "event_dated"
    assert registry.event_date_tokens(design) == {
        "full_dates": ["2021-11-15"],
        "year_months": ["2022-02"],
        "years": ["2023"],
    }


def test_timing_status_identifies_year_only_backlog():
    timeframe = {"start": 2015, "end": 2020}

    assert registry.timing_status(timeframe, {}) == "year_period_only"


def test_treaty_timing_uses_entry_into_force_not_signature():
    timeframe = {
        "start": 2008,
        "signed_date": "2008-04-07",
        "effective_date": "2008-10-01",
    }
    assert registry.timing_status(timeframe, {}) == "effective_date_only"
    assert registry.timeframe_tokens(timeframe)["full_dates"] == ["2008-10-01"]
    assert "ready_for_event_study_timing" in registry.readiness_flags(
        status=registry.timing_status(timeframe, {}),
        design={}, axes=[], inherited={},
    )


def test_registry_summary_counts_first_application_as_full_timing(monkeypatch):
    policy_dir = REPO_ROOT / "policies"
    docs = [
        (
            policy_dir / "effective_treaty.yaml",
            {"policy_id": "effective_treaty", "status": "candidate", "timeframe": {
                "start": 2016, "signed_date": "2016-11-11", "effective_date": "2017-01-01"}},
        ),
        (
            policy_dir / "signature_only_treaty.yaml",
            {"policy_id": "signature_only_treaty", "status": "candidate", "timeframe": {
                "start": 2016, "signed_date": "2016-11-11"}},
        ),
    ]
    monkeypatch.setattr(registry, "iter_policy_specs", lambda: docs)
    monkeypatch.setattr(registry.second_order, "load_axis_second_order_index", lambda: {})
    monkeypatch.setattr(registry.second_order, "load_second_order_source_families", lambda: {})

    summary = registry.build_registry()["summary"]
    assert summary["policies_with_full_event_timing"] == 1
    assert summary["timing_status_counts"] == {
        "effective_date_only": 1,
        "year_period_only": 1,
    }


def test_comparison_structure_requires_units_and_design_feature():
    design = {
        "design_features": ["controlled_vs_uncontrolled_categories"],
        "regulated_units": ["capped food"],
        "exempt_or_uncontrolled_units": ["uncapped substitutes"],
    }

    assert registry.comparison_structure_status(design) == "declared_treated_comparison_design"


def test_readiness_flags_separate_timing_from_unit_coding():
    flags = registry.readiness_flags(
        status="year_period_only",
        design={},
        axes=["regulatory.price_control_intensity"],
        inherited={"has_axis_requirements": True, "preferred_designs": ["triple_difference"]},
    )

    assert "axis_coded_treatment" in flags
    assert "needs_exact_event_dates" in flags
    assert "needs_treated_and_comparison_unit_coding" in flags
    assert "candidate_for_triple_difference_after_unit_coding" in flags
    assert registry.measurement_blockers(flags) == [
        "needs_exact_event_dates",
        "needs_treated_and_comparison_unit_coding",
    ]


def test_comparative_structure_without_outcome_plan_remains_blocked():
    flags = registry.readiness_flags(
        status="event_dated",
        design={
            "regulated_units": ["standard-rated supplies"],
            "exempt_or_uncontrolled_units": ["zero-rated supplies"],
        },
        axes=[],
        inherited={},
    )

    assert "comparative_structure_declared" in flags
    assert "needs_outcome_measurement_plan" in flags
    assert registry.measurement_blockers(flags) == ["needs_outcome_measurement_plan"]


def test_compact_policy_row_preserves_design_and_source_requirements():
    doc = {
        "policy_id": "hu_price_caps_fuel_food_2021_2023",
        "status": "candidate",
        "title": "Hungary price caps",
        "countries": ["HUN"],
        "timeframe": {"start": 2021, "end": 2023, "enacted_date": "2021-11-11"},
        "description": "Administrative cap on fuel and staple foods.",
        "axes_moved": [
            {
                "axis": "regulatory.price_control_intensity",
                "direction": "+",
                "magnitude": "strong",
                "intended": True,
            }
        ],
        "evaluation_design": {
            "design_features": ["controlled_vs_uncontrolled_categories", "triple_difference"],
            "regulated_units": ["capped fuel"],
            "exempt_or_uncontrolled_units": ["commercial fuel users"],
            "comparison_markets": ["border stations vs interior stations"],
            "event_dates": ["2021-11-15 fuel cap effective"],
            "known_data_gaps": ["station-level stockout panel"],
        },
    }
    axis_index = {
        "regulatory.price_control_intensity": {
            "has_second_order_measurement": True,
            "required_layers": [
                "first_order_price_or_transfer",
                "second_order_supply_response",
            ],
            "preferred_designs": ["triple_difference"],
            "canonical_outcomes": ["stockouts"],
        }
    }
    families = {
        "policy_event_treatment_registry": {
            "name": "Policy event and treatment-definition registry",
            "readiness": "partial_ready",
            "priority": "high",
            "layers": ["first_order_price_or_transfer"],
            "existing_fetchers": ["scripts.generate_policy_event_treatment_registry"],
        },
        "shelf_availability_stockout_surveys": {
            "name": "Shelf availability",
            "readiness": "reconstruct_needed",
            "priority": "high",
            "layers": ["second_order_supply_response"],
        },
    }

    row = registry.compact_policy_row(
        REPO_ROOT / "policies" / "hu_price_caps_fuel_food_2021_2023.yaml",
        doc,
        axis_index,
        families,
    )

    assert row["timing_status"] == "event_dated"
    assert row["comparison_structure_status"] == "declared_treated_comparison_design"
    assert row["event_date_tokens"]["full_dates"] == ["2021-11-15"]
    assert "comparative_structure_declared" in row["readiness_flags"]
    assert "known_microdata_gaps_declared" in row["readiness_flags"]
    assert row["measurement_blockers"] == ["known_microdata_gaps_declared"]
    assert row["registry_readiness"] == "needs_coding_or_data"
    assert row["source_readiness_counts"] == {
        "partial_ready": 1,
        "reconstruct_needed": 1,
    }
    assert row["source_families"][0]["family_id"] == "policy_event_treatment_registry"
