"""Publication holds accept only complete private or run-free public inputs."""
from __future__ import annotations

import pytest

from scripts import publication_rights_holds as rights


def record(hypothesis_id: str, *, visible: bool, registration: str) -> dict:
    return {
        "hypothesis_id": hypothesis_id,
        "public_visible": visible,
        "registration_status": registration,
        "tier": "calibration" if visible else "archive",
        "verdict_bucket": "supported" if visible else "missing",
        "reference_set": False,
        "estimator_floor_failures": [],
        "exclusion_reasons": [],
    }


def source(*rows: dict) -> dict:
    return {"records": list(rows), "reference_set": [], "summary": {}}


def test_private_and_run_free_public_hold_states(monkeypatch, tmp_path):
    monkeypatch.setattr(rights, "ROOT", tmp_path)
    monkeypatch.setattr(rights, "load_holds", lambda: ({"held_a", "held_b"}, 1))
    private = source(
        record("held_a", visible=True, registration="verified"),
        record("held_b", visible=False, registration="legacy_same_commit"),
    )
    assert rights.project_evidence_audit(private)["summary"]["public_visible"] == 0

    public = source(
        record("held_a", visible=False, registration="registered_no_run"),
        record("held_b", visible=False, registration="registered_no_run"),
    )
    assert rights.project_evidence_audit(public)["summary"]["public_visible"] == 0

    (tmp_path / "engine" / "runs" / "held_a").mkdir(parents=True)
    with pytest.raises(ValueError, match="run-free public projection"):
        rights.project_evidence_audit(public)


def test_incomplete_hold_projection_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(rights, "ROOT", tmp_path)
    monkeypatch.setattr(rights, "load_holds", lambda: ({"held_a", "held_b"}, 1))
    stale_registration = source(
        record("held_a", visible=False, registration="verified"),
        record("held_b", visible=False, registration="registered_no_run"),
    )
    with pytest.raises(ValueError, match="run-free public projection"):
        rights.project_evidence_audit(stale_registration)

    extra_visible = source(
        record("held_a", visible=True, registration="verified"),
        record("held_b", visible=True, registration="verified"),
    )
    with pytest.raises(ValueError, match="run-free public projection"):
        rights.project_evidence_audit(extra_visible)
