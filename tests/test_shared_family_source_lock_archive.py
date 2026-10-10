"""A shared pre-result source lock may identify failed tests, never promote them."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_evidence_tiers as tiers  # noqa: E402

MEMBERS = (
    ("fiscal", "sipri_military_burden_later_education_spending_2026"),
    ("healthcare", "sipri_military_burden_later_public_health_spending_2026"),
)
LOCK = ROOT / "data/pinned_evidence/sipri_wdi_public_budget_2026.source.json"


def case(topic: str, hypothesis_id: str):
    run_dir = ROOT / "engine/runs" / hypothesis_id
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text())
    result_path = f"engine/runs/{hypothesis_id}/diagnostics.json"
    run_commit = subprocess.check_output(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", result_path],
        cwd=ROOT, text=True,
    ).strip()
    registration = {
        "status": "verified",
        "path": f"hypotheses/{topic}/{hypothesis_id}.yaml",
        "spec_commit": diagnostics["registration_commit"],
        "run_first_commit": run_commit,
    }
    return run_dir, diagnostics, registration


def verdict(topic: str, hypothesis_id: str) -> str:
    run_dir, diagnostics, registration = case(topic, hypothesis_id)
    return tiers.immutable_source_locked_nested_verdict(
        diagnostics, hypothesis_id, run_dir, registration,
    )


def test_shared_family_lock_recognizes_only_archived_inconclusive_results():
    for topic, hypothesis_id in MEMBERS:
        assert verdict(topic, hypothesis_id) == "INCONCLUSIVE"
        _, _, registration = case(topic, hypothesis_id)
        record = tiers.build_record(ROOT / registration["path"], {hypothesis_id: registration})
        assert record["verdict_bucket"] == "inconclusive"
        assert record["tier"] == "archive"
        assert record["public_visible"] is False
        assert record["exclusion_reasons"] == ["non_result_verdict"]


def test_shared_family_lock_rejects_changed_lock_bytes():
    original = Path.read_bytes
    with patch.object(Path, "read_bytes", lambda path: b"changed" if path == LOCK else original(path)):
        assert verdict(*MEMBERS[0]) == ""


def test_shared_family_lock_rejects_changed_sibling_packet():
    sibling = ROOT / "engine/runs" / MEMBERS[1][1] / "result_card.md"
    original = Path.read_bytes
    with patch.object(Path, "read_bytes", lambda path: b"changed" if path == sibling else original(path)):
        assert verdict(*MEMBERS[0]) == ""


def test_shared_family_lock_rejects_directional_or_changed_diagnostics():
    topic, hypothesis_id = MEMBERS[0]
    run_dir, diagnostics, registration = case(topic, hypothesis_id)
    changed = {**diagnostics, "result": {**diagnostics["result"], "verdict": "SUPPORTED"}}
    assert tiers.immutable_source_locked_nested_verdict(
        changed, hypothesis_id, run_dir, registration,
    ) == ""
    changed = {**diagnostics, "source_lock_commit": "0" * 40}
    assert tiers.immutable_source_locked_nested_verdict(
        changed, hypothesis_id, run_dir, registration,
    ) == ""
