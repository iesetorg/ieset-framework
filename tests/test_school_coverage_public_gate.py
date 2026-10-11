"""Coverage must match public school scoring, not merely run-file presence."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_school_coverage_balance as coverage  # noqa: E402
import audit_scoreboard_outcomes as scoreboard  # noqa: E402


def test_archived_and_school_held_runs_are_not_tested(tmp_path, monkeypatch):
    monkeypatch.setattr(coverage, "ROOT", tmp_path)
    monkeypatch.setattr(scoreboard, "ROOT", tmp_path)
    hypothesis_dir = tmp_path / "hypotheses" / "fiscal"
    hypothesis_dir.mkdir(parents=True)
    position_dir = tmp_path / "positions"
    position_dir.mkdir()

    names = ("legacy", "hold", "mixed", "directional", "neutral", "override")
    for name in names:
        hypothesis = {"hypothesis_id": name, "evidence_type": "associational"}
        if name == "override":
            hypothesis["covers_claims"] = [{
                "position_id": "school_a", "claim_index": 5,
                "school_prediction": "supported", "polarity": "aligned",
            }]
        (hypothesis_dir / f"{name}.yaml").write_text(yaml.safe_dump(hypothesis))
        run_dir = tmp_path / "engine" / "runs" / name
        run_dir.mkdir(parents=True)
        verdict = "PARTIAL — direction inconclusive" if name == "neutral" else "SUPPORTED"
        (run_dir / "diagnostics.json").write_text(json.dumps({"verdict": verdict}))

    claims = [
        {"linked_hypothesis_id": name,
         "school_prediction": "mixed" if name in {"mixed", "override"} else "supported",
         "claim": name}
        for name in names
    ]
    claims.append(dict(claims[3]))  # One extra prediction row, same hypothesis ID.
    (position_dir / "school_a.yaml").write_text(yaml.safe_dump({
        "position_id": "school_a", "school": "School A",
        "falsifiable_specific_claims": claims,
    }))
    (position_dir / "control.yaml").write_text(yaml.safe_dump({
        "position_id": "control", "school": "Control",
        "scoreboard_role": "benchmark_control",
        "falsifiable_specific_claims": [claims[3]],
    }))
    timing = {}
    for index, claim in enumerate(claims):
        prediction = "supported" if index == 5 else claim["school_prediction"]
        timing[f"school_a#{index}"] = {
            "eligible": True, "position_id": "school_a", "claim_index": index,
            "hypothesis_id": claim["linked_hypothesis_id"], "claim": claim["claim"],
            "scope": None, "school_prediction": prediction, "polarity": "aligned",
        }
    timing["control#0"] = {
        **timing["school_a#3"], "position_id": "control", "claim_index": 0,
    }
    monkeypatch.setattr(coverage, "load_school_timing_index", lambda: timing)
    evidence = {
        name: {
            "public_visible": name != "legacy",
            "school_score_eligible": name != "hold",
            "tier": "archive" if name == "legacy" else "calibration",
            "registration_status": "legacy_same_commit" if name == "legacy" else "verified",
            "exclusion_reasons": ["registration_legacy_same_commit"] if name == "legacy" else [],
        }
        for name in names
    }

    audit = coverage.audit_coverage(1, 1, directional_target=6, evidence_index=evidence)
    row = audit["schools"][0]
    assert audit["summary"]["schools"] == 1
    assert audit["summary"]["benchmark_controls"] == 1
    assert row["unique_hypotheses"] == 6
    assert row["unique_public"] == 5
    assert row["unique_school_score_eligible"] == 4
    assert row["unique_tested"] == 4
    assert row["scoreboard_tested_claims"] == 5
    assert row["unique_neutral_tested"] == 2
    assert row["unique_directional_linked"] == 5
    assert row["unique_directional_scored"] == 2
    assert row["scoreboard_directional_scored_claims"] == 3
    assert row["duplicate_claim_links"] == 1
    assert row["directional_gap_to_target"] == 4
    assert row["minimum_new_directional_claims_for_target"] == 1
    assert row["unique_archived"] == 1
    assert row["public_school_score_holds"] == 1
    assert row["directional_blockers"] == {
        "neutral_result": 1,
        "registration_legacy_same_commit": 1,
        "school_score_eligible_false": 1,
    }
    queued = {item["hypothesis_id"] for item in audit["directional_queue"]["school_a"]}
    assert queued == {"legacy", "hold", "neutral"}
    output = tmp_path / "coverage"
    coverage.write_outputs(audit, output)
    with output.with_suffix(".csv").open(newline="") as handle:
        queue_rows = list(csv.DictReader(handle))
    assert {item["hypothesis_id"] for item in queue_rows} == queued
    assert {item["position_id"] for item in queue_rows} == {"school_a"}
    assert "directional_queue" not in json.loads(output.with_suffix(".json").read_text())


def test_markdown_discloses_gate_and_directional_target(tmp_path):
    audit = {
        "generated_at": "2026-10-11",
        "methodology": {
            "v1_floor": {"unique_hypotheses": 100, "unique_tested": 60},
            "stretch_floor": {"unique_hypotheses": 125, "unique_tested": 80},
            "directional_target": 200,
        },
        "summary": {
            "schools": 0, "benchmark_controls": 0, "balanced_v1": 0,
            "under_covered": 0, "linked_range": [0, 0], "tested_range": [0, 0],
            "directional_scored_range": [0, 0], "total_directional_gap_to_target": 0,
            "minimum_new_directional_claims_for_target": 0,
            "total_linked_gap_to_floor": 0, "total_tested_gap_to_floor": 0,
        },
        "schools": [], "directional_queue": {},
    }
    output = tmp_path / "coverage"
    coverage.write_outputs(audit, output)
    text = output.with_suffix(".md").read_text()
    assert "visible run file alone does not qualify" in text
    assert "cannot become preregistered by relabeling" in text
    assert "Path to 200 Directional Scored Tests" in text
