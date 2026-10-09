"""Python scoreboard audits must use the same strict public evidence gate."""
from __future__ import annotations

import sys

import yaml
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


def test_pcw100_all_seventeen_historical_links_are_unscored_everywhere():
    hypothesis_id = "pcw100_us_mw_bite_ratio_p10_wage"
    evidence = scoreboard.live_evidence_index()[hypothesis_id]
    assert evidence["public_visible"] is True
    assert evidence["school_score_eligible"] is False

    hypothesis_path = ROOT / "hypotheses" / "distribution" / f"{hypothesis_id}.yaml"
    hypothesis = yaml.safe_load(hypothesis_path.read_text(encoding="utf-8"))
    expected_links = {
        (entry["position_id"], entry["claim_index"])
        for entry in hypothesis["covers_claims"]
    }
    assert len(expected_links) == 17

    for position_id, claim_index in expected_links:
        position = yaml.safe_load((ROOT / "positions" / f"{position_id}.yaml").read_text(encoding="utf-8"))
        claim = position["falsifiable_specific_claims"][claim_index]
        assert claim["linked_hypothesis_id"] == hypothesis_id
        assert claim["empirical_status"] == "untested"

    audit = scoreboard.score_positions()
    unscored_links = {
        (row["position_id"], row["claim_index"])
        for row in audit["unscored_public_links"]
        if row["hypothesis_id"] == hypothesis_id
    }
    assert unscored_links == expected_links
    assert audit["school_scored_public_links"] + len(audit["unscored_public_links"]) == audit["public_claim_links"]

    gate = gates.build_gate_index(scope="all")
    rows = [row for row in gate["claim_links"] if row["hypothesis_id"] == hypothesis_id]
    assert {(row["position_id"], row["claim_index"]) for row in rows} == expected_links
    for row in rows:
        assert row["verdict_public"] is True
        assert row["school_score_eligible"] is False
        assert row["raw_school_outcome"] == "untested"
        assert row["raw_weighted_score"] == 0.0
        assert row["recommended_weighted_score_after_gates"] == 0.0
        assert row["declared_scoreboard_eligible"] is False
        assert row["strict_scoreboard_eligible"] is False
        assert row["declared_gate_status"] == "school_score_hold"
        assert row["strict_gate_status"] == "school_score_hold"
