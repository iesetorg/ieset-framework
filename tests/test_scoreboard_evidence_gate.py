"""Python scoreboard audits must use the same strict public evidence gate."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_scoreboard_outcomes as scoreboard  # noqa: E402
import audit_second_order_measurement as second_order  # noqa: E402
import generate_scoreboard_second_order_gates as gates  # noqa: E402


def test_legacy_run_with_real_verdict_is_not_public():
    hypothesis_id = "soviet_union_central_planning_gdp_collapse_1989_1991"
    evidence = scoreboard.live_evidence_index()
    assert evidence[hypothesis_id]["public_visible"] is False
    is_public, verdict = scoreboard.hypothesis_public_verdict(
        hypothesis_id, {hypothesis_id: {}}, evidence
    )
    assert verdict and verdict.lower().startswith("supported")
    assert is_public is False


def test_rescoped_screen_has_at_most_quarter_weight():
    row = gates.build_claim_gate_row(
        position_id="example_school",
        claim_index=0,
        claim={
            "linked_hypothesis_id": "rescoped_screen",
            "school_prediction": "supported",
        },
        hypothesis={"evidence_type": "associational"},
        coverage={},
        is_public=True,
        verdict="SUPPORTED",
        scope="all",
        scoreboard_weight_cap=0.25,
    )
    assert row["evidence_weight"] == 0.25
    assert row["raw_weighted_score"] == 0.25


def test_strict_second_order_contract_applies_to_policy_experiments():
    descriptive = {
        "claim": "The observed GDP series rose over this period.",
        "variables": {"outcome": [{"name": "gdp"}]},
        "scope": {"policy_family": ["none"]},
    }
    policy_experiment = {
        "claim": "A specified intervention changes employment.",
        "variables": {"treatment": [{"name": "intervention"}]},
    }
    outside = second_order.second_order_gate_for_hypothesis(
        descriptive, "all", strict_missing_contract=True
    )
    inside = second_order.second_order_gate_for_hypothesis(
        policy_experiment, "all", strict_missing_contract=True
    )
    assert outside["gate_status"] == "out_of_scope"
    assert outside["scoreboard_eligible"] is True
    assert inside["gate_status"] == "missing_contract_hold"
    assert inside["scoreboard_eligible"] is False
