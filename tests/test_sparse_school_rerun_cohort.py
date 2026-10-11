"""The sparse-school rerun queue must preserve the registration/public gates."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import plan_sparse_school_reruns as reruns  # noqa: E402


def registration(*, verified=True, same_commit=False):
    return {
        "status": "verified" if verified else "legacy_same_commit",
        "verified": verified,
        "spec_commit": "a" * 40,
        "run_first_commit": "a" * 40 if same_commit else "b" * 40,
        "spec_committed_at": "2026-01-01T00:00:00+00:00",
        "run_committed_at": "2026-02-01T00:00:00+00:00",
        "path": "hypotheses/fiscal/example.yaml",
    }


def row(school, hypothesis_id, *, status="verified", tier="archive", blockers="estimator_floor_failed"):
    return {
        "position_id": school,
        "hypothesis_id": hypothesis_id,
        "registration_status": status,
        "evidence_tier": tier,
        "prediction": "supported",
        "blockers": blockers,
    }


def test_cohort_excludes_legacy_public_and_same_commit(monkeypatch, tmp_path):
    monkeypatch.setattr(reruns, "frozen_spec_drift", lambda root, reg: [] if reg["spec_commit"] == "a" * 40 else ["variables"])
    monkeypatch.setattr(reruns, "before_run_spec_status", lambda root, reg: "candidate" if reg.get("draft_case") else "pre_registered")
    registrations = {
        "frozen": registration(),
        "timing_only": {**registration(), "draft_case": True},
        "legacy": registration(verified=False),
        "same_commit": registration(same_commit=True),
        "public": registration(),
    }
    rows = [
        row("degrowth", "frozen"), row("mmt", "frozen"),
        row("degrowth", "timing_only"),
        row("degrowth", "legacy", status="legacy_same_commit"),
        row("degrowth", "same_commit"),
        row("degrowth", "public", tier="calibration"),
    ]
    coverage = [
        {"position_id": "degrowth", "unique_directional_scored": 3},
        {"position_id": "mmt", "unique_directional_scored": 8},
    ]
    cohort = reruns.build_cohort(rows, registrations, root=tmp_path,
                                  schools=("degrowth", "mmt", "new_keynesian"),
                                  coverage_rows=coverage)
    assert cohort["summary"]["unique_candidates"] == 2
    assert cohort["summary"]["school_links"] == 3
    assert cohort["summary"]["explicit_preregistered_status"] == 1
    assert cohort["summary"]["draft_or_candidate_status_before_run"] == 1
    assert cohort["summary"]["ready_to_score"] == 0
    assert [school["timing_verified_archived_directional_links"] for school in cohort["schools"]] == [2, 1, 0]
    assert cohort["schools"][0]["explicit_preregistered_status_links"] == 1
    assert cohort["schools"][0]["upper_bound_if_cohort_clears"] == 5
    assert cohort["schools"][0]["gap_after_cohort_upper_bound"] == 195
    assert {c["hypothesis_id"]: c["school_links"] for c in cohort["candidates"]}["frozen"] == ["degrowth", "mmt"]
    assert all(candidate["ready_to_score"] is False for candidate in cohort["candidates"])
    output = tmp_path / "queue"
    reruns.write_outputs(cohort, output)
    assert "blocked engineering queue" in output.with_suffix(".md").read_text()


def test_changed_fields_stay_blocked_and_missing_blocker_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(reruns, "frozen_spec_drift", lambda root, reg: ["falsification"])
    monkeypatch.setattr(reruns, "before_run_spec_status", lambda root, reg: "pre_registered")
    cohort = reruns.build_cohort(
        [row("degrowth", "changed", blockers="external_integrity_quarantine;estimator_floor_failed")],
        {"changed": registration()}, root=tmp_path, schools=("degrowth",),
    )
    candidate = cohort["candidates"][0]
    assert candidate["next_action"] == "review_first_committed_spec_or_register_new_id"
    assert candidate["frozen_field_drift"] == ["falsification"]
    assert candidate["blockers"] == ["estimator_floor_failed", "external_integrity_quarantine"]
    assert candidate["estimated_score_gain_now"] == 0
    assert cohort["schools"][0]["changed_since_first_registration"] == 1
    try:
        reruns.build_cohort(
            [row("degrowth", "changed", blockers="")],
            {"changed": registration()}, root=tmp_path, schools=("degrowth",),
        )
    except ValueError as exc:
        assert "lacks a public-gate blocker" in str(exc)
    else:
        raise AssertionError("an archived row without a blocker must not be queued")


def test_status_is_read_from_git_tree_before_first_run(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True).strip()

    git("init", "-q")
    git("config", "user.name", "IESET Test")
    git("config", "user.email", "ieset-test@example.invalid")
    for name, status in (("draft_case", "candidate"), ("registered_case", "pre_registered")):
        spec = tmp_path / "hypotheses" / "fiscal" / f"{name}.yaml"
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(f"hypothesis_id: {name}\nstatus: {status}\n")
        git("add", str(spec.relative_to(tmp_path)))
        git("commit", "-qm", f"spec {name}")
        run = tmp_path / "engine" / "runs" / name / "diagnostics.json"
        run.parent.mkdir(parents=True, exist_ok=True)
        run.write_text("{}\n")
        git("add", str(run.relative_to(tmp_path)))
        git("commit", "-qm", f"run {name}")
        observed = reruns.before_run_spec_status(tmp_path, {
            "path": str(spec.relative_to(tmp_path)),
            "run_first_commit": git("rev-parse", "HEAD"),
        })
        assert observed == status
