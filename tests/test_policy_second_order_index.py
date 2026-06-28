from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_policy_second_order_index as index  # noqa: E402


def test_source_family_details_expands_fetcher_readiness():
    families = {
        "retail_scanner_price_quantity_panel": {
            "name": "Retail scanner price and quantity panels",
            "readiness": "proprietary_gap",
            "priority": "high",
            "publisher_refs": [],
            "existing_fetchers": [],
        },
        "national_building_permits_completions": {
            "name": "Building permits and housing completions",
            "readiness": "partial_ready",
            "priority": "high",
            "publisher_refs": ["us_census"],
            "existing_fetchers": ["data.fetchers.us_census"],
        },
    }

    details = index.source_family_details(
        ["national_building_permits_completions", "retail_scanner_price_quantity_panel"],
        families,
    )

    assert details == [
        {
            "family_id": "national_building_permits_completions",
            "name": "Building permits and housing completions",
            "readiness": "partial_ready",
            "priority": "high",
            "publisher_refs": ["us_census"],
            "existing_fetchers": ["data.fetchers.us_census"],
        },
        {
            "family_id": "retail_scanner_price_quantity_panel",
            "name": "Retail scanner price and quantity panels",
            "readiness": "proprietary_gap",
            "priority": "high",
            "publisher_refs": [],
            "existing_fetchers": [],
        },
    ]


def test_compact_policy_row_preserves_explicit_and_inherited_designs():
    row = {
        "id": "hu_price_caps_fuel_food_2021_2023",
        "path": "policies/hu_price_caps_fuel_food_2021_2023.yaml",
        "status": "candidate",
        "control_focus": True,
        "axes": ["regulatory.price_control_intensity"],
        "has_evaluation_design": True,
        "evaluation_design_status": "explicit",
        "design_features": ["controlled_vs_uncontrolled_categories"],
        "known_data_gaps": ["scanner data"],
        "axis_inherited_requirements": {
            "required_layers": ["first_order_price_or_transfer", "second_order_supply_response"],
            "preferred_designs": ["triple_difference"],
            "canonical_outcomes": ["stockouts"],
            "source_readiness_counts": {"partial_ready": 1, "proprietary_gap": 1},
            "source_families": ["retail_scanner_price_quantity_panel"],
        },
    }
    families = {
        "retail_scanner_price_quantity_panel": {
            "name": "Retail scanner price and quantity panels",
            "readiness": "proprietary_gap",
            "priority": "high",
            "publisher_refs": [],
            "existing_fetchers": [],
        },
    }

    compact = index.compact_policy_row(row, families)

    assert compact["policy_id"] == "hu_price_caps_fuel_food_2021_2023"
    assert compact["has_evaluation_design"] is True
    assert compact["evaluation_design_status"] == "explicit"
    assert compact["explicit_design_features"] == ["controlled_vs_uncontrolled_categories"]
    assert compact["required_layers"] == [
        "first_order_price_or_transfer",
        "second_order_supply_response",
    ]
    assert compact["source_families"][0]["family_id"] == "retail_scanner_price_quantity_panel"
