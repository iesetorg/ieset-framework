from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_scoreboard_second_order_gates as gates  # noqa: E402


def test_failure_credit_is_weak_for_broad_associational_failure_win():
    credit = gates.failure_credit_for_claim(
        school_prediction="falsified",
        outcome="supports_position",
        evidence_type="associational",
        hypothesis={"hypothesis_id": "broad_panel"},
        declared_gate={"scoreboard_eligible": True},
        strict_gate={"scoreboard_eligible": True},
    )

    assert credit["kind"] == "weak_associational_failure_credit"
    assert credit["recommended_multiplier"] == 0.25


def test_failure_credit_is_zero_when_second_order_gate_holds():
    credit = gates.failure_credit_for_claim(
        school_prediction="falsified",
        outcome="supports_position",
        evidence_type="causal",
        hypothesis={
            "mechanism_measurement": {
                "design_features": ["triple_difference"],
                "causal_layers": [
                    {
                        "layer": "second_order_supply_response",
                        "measurement_status": "measured",
                        "required_for_dispositive_verdict": True,
                    }
                ],
            }
        },
        declared_gate={"scoreboard_eligible": False},
        strict_gate={"scoreboard_eligible": False},
    )

    assert credit["kind"] == "second_order_gate_hold"
    assert credit["recommended_multiplier"] == 0.0


def test_claim_gate_row_separates_raw_outcome_from_promotion_eligibility():
    row = gates.build_claim_gate_row(
        position_id="example_school",
        claim_index=3,
        claim={
            "claim": "Rent control failure validates this school only if supply response is measured.",
            "linked_hypothesis_id": "rent_control_probe",
            "school_prediction": "falsified",
            "claim_polarity": "aligned",
        },
        hypothesis={
            "hypothesis_id": "rent_control_probe",
            "claim": "Rent control improves affordability without reducing supply.",
            "evidence_type": "causal",
            "mechanism_measurement": {
                "promotion_gate": "screen_only_until_second_order_measured",
                "design_features": ["triple_difference"],
                "causal_layers": [
                    {
                        "layer": "second_order_supply_response",
                        "measurement_status": "data_gap",
                        "required_for_dispositive_verdict": True,
                    }
                ],
            },
        },
        coverage={},
        is_public=True,
        verdict="REFUTED - supply fell",
        scope="controls",
    )

    assert row["raw_school_outcome"] == "supports_position"
    assert row["declared_scoreboard_eligible"] is False
    assert row["strict_scoreboard_eligible"] is False
    assert row["failure_credit_kind"] == "second_order_gate_hold"
    assert row["recommended_weighted_score_after_gates"] == 0.0
    assert row["required_data_gaps"] == ["second_order_supply_response"]
