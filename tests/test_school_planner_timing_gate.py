"""Planning counts must match the advance school-score gate."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plan_school_coverage_run_queue as run_queue  # noqa: E402
import plan_school_tested_equalization as equalization  # noqa: E402


def fixture_rows(tmp_path: Path):
    position_dir = tmp_path / "positions"
    position_dir.mkdir()
    names = (
        "advance_public", "historical_public", "school_held_public",
        "advance_hidden", "historical_hidden", "neutral_public", "future_no_run",
    )
    claims = [
        {"claim": name, "linked_hypothesis_id": name,
         "school_prediction": "mixed" if name == "neutral_public" else "supported"}
        for name in names
    ]
    (position_dir / "school.yaml").write_text(yaml.safe_dump({
        "position_id": "school", "falsifiable_specific_claims": claims,
    }))
    (position_dir / "control.yaml").write_text(yaml.safe_dump({
        "position_id": "control", "scoreboard_role": "benchmark_control",
        "falsifiable_specific_claims": [claims[0]],
    }))
    hypotheses = {name: {"hypothesis_id": name} for name in names}
    evidence = {
        name: {"public_visible": name.endswith("public"),
               "school_score_eligible": name != "school_held_public",
               "registration_status": "registered_no_run" if name == "future_no_run" else "verified"}
        for name in names
    }
    timing = {
        f"school#{index}": {
            "eligible": name not in {"historical_public", "historical_hidden", "future_no_run"},
            "position_id": "school", "claim_index": index,
            "hypothesis_id": name, "claim": name, "scope": None,
            "school_prediction": claim["school_prediction"], "polarity": "aligned",
        }
        for index, (name, claim) in enumerate(zip(names, claims))
    }

    def public_verdict(hypothesis_id, _hypotheses, _evidence):
        return evidence[hypothesis_id]["public_visible"], "SUPPORTED"

    return hypotheses, evidence, timing, public_verdict


def test_equalization_excludes_historical_public_results_and_control(tmp_path, monkeypatch):
    hypotheses, evidence, timing, public_verdict = fixture_rows(tmp_path)
    monkeypatch.setattr(equalization, "ROOT", tmp_path)
    monkeypatch.setattr(equalization, "build_hypothesis_index", lambda: (hypotheses, {}))
    monkeypatch.setattr(equalization, "live_evidence_index", lambda: evidence)
    monkeypatch.setattr(equalization, "load_school_timing_index", lambda: timing)
    monkeypatch.setattr(equalization, "load_axis_index", lambda: {})
    monkeypatch.setattr(equalization, "hypothesis_public_verdict", public_verdict)
    monkeypatch.setattr(equalization, "visibility_status", lambda *_: {"reason": "needs_successful_rerun"})

    plan = equalization.build_plan(4)
    assert plan["summary"]["schools"] == 1
    school = plan["schools"][0]
    assert school["tested_predictions"] == 2  # A neutral advance result is tested.
    assert school["public_timing_holds"] == 1
    assert school["public_school_score_holds"] == 1
    assert school["hidden_linked_predictions"] == 3
    assert school["pre_run_hidden_predictions"] == 1
    assert school["future_registered_predictions"] == 1
    assert school["repair_existing_hidden_to_target"] == 1
    assert school["new_link_or_new_hypothesis_gap_after_repairs"] == 1
    assert [row["hypothesis_id"] for row in plan["repair_queue"]] == ["advance_hidden"]


def test_run_queue_only_prioritizes_advance_hidden_result(tmp_path, monkeypatch):
    hypotheses, evidence, timing, public_verdict = fixture_rows(tmp_path)
    monkeypatch.setattr(run_queue, "ROOT", tmp_path)
    monkeypatch.setattr(run_queue, "hypothesis_public_verdict", public_verdict)

    states = run_queue.collect_position_states(
        hypotheses, 1, 4, evidence_index=evidence,
        timing_index=timing, coverage_index={},
    )
    assert set(states) == {"school"}
    assert states["school"]["tested"] == ["advance_public", "neutral_public"]
    assert states["school"]["pending"] == ["advance_hidden"]
    assert states["school"]["tested_gap"] == 2
    assert states["school"]["blocked_claim_reasons"] == {
        "school_prediction_not_pre_run": 2,
        "school_score_eligible_false": 1,
        "awaiting_first_run": 1,
    }
