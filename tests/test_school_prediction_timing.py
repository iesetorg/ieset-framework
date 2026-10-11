"""A school forecast needs an exact reciprocal link before the first run."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_school_prediction_timing as timing  # noqa: E402


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def save_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def test_reciprocal_forecast_must_precede_run_and_keep_scope(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    position_path = tmp_path / "positions" / "school.yaml"
    spec_path = tmp_path / "hypotheses" / "growth" / "study.yaml"
    first = {
        "claim": "A defined exposure increases the outcome.",
        "linked_hypothesis_id": "study",
        "school_prediction": "supported",
        "scope": {"period": [2020, 2022]},
    }
    second = {
        "claim": "A second exposure decreases the outcome.",
        "linked_hypothesis_id": "study",
        "school_prediction": "falsified",
        "scope": {"period": [2020, 2022]},
    }
    save_yaml(position_path, {"position_id": "school", "falsifiable_specific_claims": [first]})
    spec = {
        "hypothesis_id": "study",
        "covers_claims": [{
            "position_id": "school", "claim_index": 0,
            "school_prediction": "supported", "polarity": "aligned",
        }],
    }
    save_yaml(spec_path, spec)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "freeze forecast")
    (tmp_path / "engine" / "runs" / "study").mkdir(parents=True)
    (tmp_path / "engine" / "runs" / "study" / "diagnostics.json").write_text("{}")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "run study")
    run_commit = git(tmp_path, "rev-parse", "HEAD")
    registration = {"study": {
        "path": "hypotheses/growth/study.yaml",
        "status": "verified", "verified": True,
        "run_first_commit": run_commit,
    }}
    first_manifest = timing.build_manifest(tmp_path, registration)
    assert first_manifest["rows"]["school#0"]["eligible"] is True

    save_yaml(position_path, {
        "position_id": "school", "falsifiable_specific_claims": [first, second],
    })
    spec["covers_claims"].append({
        "position_id": "school", "claim_index": 1,
        "school_prediction": "falsified", "polarity": "aligned",
    })
    save_yaml(spec_path, spec)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "attach later school claim")
    later = timing.build_manifest(tmp_path, registration)
    assert later["rows"]["school#0"]["eligible"] is True
    assert later["rows"]["school#1"]["eligible"] is False
    assert later["rows"]["school#1"]["status"] == "both_added_or_changed_after_run"

    first["scope"] = {"period": [2020, 2023]}
    save_yaml(position_path, {
        "position_id": "school", "falsifiable_specific_claims": [first, second],
    })
    changed = timing.build_manifest(tmp_path, registration)
    assert changed["rows"]["school#0"]["status"] == "position_added_or_changed_after_run"
    assert changed["rows"]["school#0"]["eligible"] is False


def test_public_projection_removes_held_claims(tmp_path: Path) -> None:
    path = tmp_path / "holds.json"
    path.write_text(json.dumps({
        "schema": "ieset-publication-rights-holds-v1",
        "status": "active_publication_hold",
        "groups": [{"count": 1, "hypothesis_ids": ["held_study"]}],
    }))
    held = timing.public_held_ids(path)
    manifest = {
        "schema": timing.SCHEMA,
        "rows": {
            "school#0": {"hypothesis_id": "held_study", "status": "prospective_reciprocal", "eligible": True},
            "school#1": {"hypothesis_id": "safe_study", "status": "prospective_reciprocal", "eligible": True},
        },
    }
    projected = timing.public_projection(manifest, held)
    assert list(projected["rows"]) == ["school#1"]
    assert projected["eligible_claims"] == ["school#1:safe_study"]
    assert "held_study" not in json.dumps(projected)
    with pytest.raises(ValueError):
        timing.public_held_ids(tmp_path / "missing.json")
