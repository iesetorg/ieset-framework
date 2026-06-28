from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import audit_second_order_measurement as audit  # noqa: E402


def test_summarize_layers_collects_required_gaps_and_sources():
    summary = audit.summarize_layers(
        {
            "promotion_gate": "screen_only_until_second_order_measured",
            "causal_layers": [
                {
                    "layer": "first_order_price_or_transfer",
                    "measurement_status": "measured",
                    "required_for_dispositive_verdict": True,
                },
                {
                    "layer": "second_order_supply_response",
                    "measurement_status": "data_gap",
                    "required_for_dispositive_verdict": True,
                    "candidate_sources": ["building permits", "listings microdata"],
                },
                {
                    "layer": "distributional_incidence",
                    "measurement_status": "data_gap",
                    "required_for_dispositive_verdict": False,
                    "candidate_sources": ["tenant registry"],
                },
            ],
        }
    )

    assert summary["has_contract"] is True
    assert summary["promotion_gate"] == "screen_only_until_second_order_measured"
    assert summary["required_data_gaps"] == ["second_order_supply_response"]
    assert summary["status_counts"] == {"measured": 1, "data_gap": 2}
    assert summary["candidate_sources"] == [
        "building permits",
        "listings microdata",
        "tenant registry",
    ]


def test_declared_screen_only_gate_holds_scoreboard_claim():
    doc = {
        "hypothesis_id": "rent_control_probe",
        "claim": "Rent control reduces housing supply through investment response.",
        "mechanism_measurement": {
            "promotion_gate": "screen_only_until_second_order_measured",
            "causal_layers": [
                {
                    "layer": "second_order_supply_response",
                    "measurement_status": "data_gap",
                    "required_for_dispositive_verdict": True,
                }
            ],
        },
    }

    gate = audit.second_order_gate_for_hypothesis(doc, "controls")

    assert gate["scoreboard_eligible"] is False
    assert gate["gate_status"] == "declared_measurement_hold"
    assert gate["required_data_gaps"] == ["second_order_supply_response"]


def test_missing_contract_is_flagged_unless_strict_mode_is_enabled():
    doc = {
        "hypothesis_id": "price_control_probe",
        "claim": "Price controls create shortage pressure.",
        "variables": {"treatment": "price_control"},
    }

    non_strict = audit.second_order_gate_for_hypothesis(doc, "controls")
    strict = audit.second_order_gate_for_hypothesis(doc, "controls", strict_missing_contract=True)

    assert non_strict["scoreboard_eligible"] is True
    assert non_strict["gate_status"] == "missing_contract_flag"
    assert strict["scoreboard_eligible"] is False
    assert strict["gate_status"] == "missing_contract_hold"


def test_out_of_scope_hypothesis_is_not_second_order_gated():
    doc = {
        "hypothesis_id": "non_policy_probe",
        "claim": "Mountain altitude predicts average temperature.",
    }

    gate = audit.second_order_gate_for_hypothesis(doc, "controls", strict_missing_contract=True)

    assert gate["scoreboard_eligible"] is True
    assert gate["gate_status"] == "out_of_scope"


def test_source_family_readiness_maps_free_form_gap_labels():
    families = {
        "national_building_permits_completions": {
            "name": "Building permits and housing completions",
            "readiness": "partial_ready",
            "priority": "high",
            "publisher_refs": ["us_census"],
            "existing_fetchers": ["data.fetchers.us_census"],
            "aliases": ["building permit", "completion"],
        },
        "retail_scanner_price_quantity_panel": {
            "name": "Retail scanner price and quantity panels",
            "readiness": "proprietary_gap",
            "priority": "high",
            "publisher_refs": [],
            "existing_fetchers": [],
            "aliases": ["scanner data", "retailer margin"],
        },
    }
    source_counts = {
        "national building-permit and completion registers": 2,
        "capped vs uncapped category scanner data": 1,
        "unmapped regulator notebook": 1,
    }

    readiness = audit.audit_source_family_readiness(source_counts, families)

    assert readiness["registered_source_families"] == 2
    assert readiness["mentioned_source_families"] == 2
    assert readiness["mentions_by_readiness"] == {
        "partial_ready": 1,
        "proprietary_gap": 1,
    }
    assert readiness["source_families"][0]["family_id"] == "national_building_permits_completions"
    assert readiness["unmatched_candidate_sources"] == [("unmapped regulator notebook", 1)]


def test_axis_inherited_requirements_roll_up_layers_designs_and_sources():
    axis_index = {
        "regulatory.housing_rent_control": {
            "has_second_order_measurement": True,
            "required_layers": ["second_order_supply_response", "distributional_incidence"],
            "preferred_designs": ["triple_difference", "welfare_accounting"],
            "canonical_outcomes": ["regulated vs exempt rents"],
        },
        "fiscal.spending_level": {
            "has_second_order_measurement": False,
        },
    }
    families = {
        "national_building_permits_completions": {
            "layers": ["second_order_supply_response"],
            "readiness": "partial_ready",
        },
        "household_distributional_microdata": {
            "layers": ["distributional_incidence"],
            "readiness": "partial_ready",
        },
        "retail_scanner_price_quantity_panel": {
            "layers": ["leakage_or_substitution"],
            "readiness": "proprietary_gap",
        },
    }

    inherited = audit.inherited_axis_requirements(
        ["regulatory.housing_rent_control", "fiscal.spending_level"],
        axis_index,
        families,
    )

    assert inherited["has_axis_requirements"] is True
    assert inherited["axes_with_requirements"] == ["regulatory.housing_rent_control"]
    assert inherited["missing_axis_guidance"] == ["fiscal.spending_level"]
    assert inherited["required_layers"] == [
        "distributional_incidence",
        "second_order_supply_response",
    ]
    assert inherited["preferred_designs"] == ["triple_difference", "welfare_accounting"]
    assert inherited["source_families"] == [
        "household_distributional_microdata",
        "national_building_permits_completions",
    ]
    assert inherited["source_readiness_counts"] == {"partial_ready": 2}


def test_aggregate_policy_axis_requirements_counts_missing_explicit_designs():
    rows = [
        {
            "id": "a",
            "path": "policies/a.yaml",
            "status": "candidate",
            "axes": ["regulatory.housing_rent_control"],
            "control_focus": True,
            "evaluation_design_status": "axis_inherited_missing_explicit_design",
            "axis_inherited_requirements": {
                "has_axis_requirements": True,
                "required_layers": ["second_order_supply_response"],
                "source_families": ["national_building_permits_completions"],
                "source_readiness_counts": {"partial_ready": 1},
            },
        },
        {
            "id": "b",
            "path": "policies/b.yaml",
            "status": "candidate",
            "axes": ["fiscal.tax_progressivity"],
            "control_focus": False,
            "evaluation_design_status": "explicit",
            "axis_inherited_requirements": {
                "has_axis_requirements": True,
                "required_layers": ["distributional_incidence"],
                "source_families": ["household_distributional_microdata"],
                "source_readiness_counts": {"partial_ready": 1},
            },
        },
    ]

    summary = audit.aggregate_policy_axis_requirements(rows)

    assert summary["policies_with_axis_requirements"] == 2
    assert summary["policies_missing_explicit_design_but_axis_requirements"] == 1
    assert summary["evaluation_design_status_counts"] == {
        "axis_inherited_missing_explicit_design": 1,
        "explicit": 1,
    }
    assert summary["required_layer_policy_mentions"] == {
        "second_order_supply_response": 1,
        "distributional_incidence": 1,
    }
    assert summary["source_readiness_policy_mentions"] == {"partial_ready": 2}
