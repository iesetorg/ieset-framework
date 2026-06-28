from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_second_order_test_backlog as backlog  # noqa: E402


def test_inferred_layers_for_price_control_include_welfare_and_quality():
    doc = {
        "hypothesis_id": "price_control_probe",
        "claim": "Binding food price controls reduce prices but create shortages and quality degradation.",
        "scope": {"policy_family": ["regulation"], "treatment_tags": ["price_controls"]},
    }

    layers = backlog.inferred_layers_for_hypothesis(doc)

    assert "first_order_price_or_transfer" in layers
    assert "leakage_or_substitution" in layers
    assert "quality_margin" in layers
    assert "net_welfare" in layers
    assert "distributional_incidence" in layers


def test_missing_layers_prefer_declared_gate_gaps_over_inference():
    doc = {
        "hypothesis_id": "rent_control_probe",
        "claim": "Rent control effects.",
        "mechanism_measurement": {
            "causal_layers": [
                {
                    "layer": "second_order_supply_response",
                    "measurement_status": "data_gap",
                    "required_for_dispositive_verdict": True,
                }
            ]
        },
    }
    gate_rows = [
        {
            "required_data_gaps": ["net_welfare"],
        }
    ]

    layers, source = backlog.missing_layers_for_hypothesis(doc, gate_rows)

    assert layers == ["net_welfare", "second_order_supply_response"]
    assert source == "declared_contract_or_gate"


def test_recommended_designs_include_requested_patterns():
    designs = backlog.recommended_designs_for_layers(
        [
            "first_order_price_or_transfer",
            "second_order_supply_response",
            "distributional_incidence",
            "net_welfare",
        ]
    )

    assert "controlled_vs_uncontrolled_categories" in designs
    assert "triple_difference" in designs
    assert "distributional_decomposition" in designs
    assert "welfare_accounting" in designs


def test_source_family_details_filters_by_policy_domain():
    families = {
        "household_distributional_microdata": {
            "name": "Household distribution",
            "layers": ["distributional_incidence"],
            "policy_domains": ["tax_policy", "welfare_policy"],
            "readiness": "partial_ready",
        },
        "education_quality_attainment_panel": {
            "name": "Education outcomes",
            "layers": ["distributional_incidence"],
            "policy_domains": ["education_policy"],
            "readiness": "partial_ready",
        },
    }

    details = backlog.source_family_details(
        ["distributional_incidence"],
        families,
        {"tax_policy"},
    )

    assert [row["family_id"] for row in details] == ["household_distributional_microdata"]


def test_declared_price_control_domains_override_broad_policy_families():
    doc = {
        "claim": "Price controls with fiscal and monetary confounders.",
        "scope": {"policy_family": ["fiscal_policy", "monetary_policy", "regulation"]},
        "mechanism_measurement": {"mechanism_type": "price_control"},
    }

    domains = backlog.policy_domains_for_hypothesis(doc)

    assert "price_control" in domains
    assert "monetary_policy" not in domains
    assert "public_spending" not in domains
