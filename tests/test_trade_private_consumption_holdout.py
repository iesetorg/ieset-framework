"""Custody and read-only replay checks for the prospective trade holdout."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_trade_openness_private_consumption_geographic_holdout_v2 as holdout  # noqa: E402


def test_private_consumption_gate_covers_all_four_sources_and_nine_tests() -> None:
    gate = holdout.gate_from_spec(holdout.frozen_spec())
    assert gate["family_size"] == 9
    assert gate["p_max"] == 0.01
    assert len(gate["source_files"]) == 4
    assert len(holdout.FAMILY_SPECS) == 9


def test_read_only_check_detects_stored_packet_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(holdout, "RUN_DIR", tmp_path / "run")
    state = {
        "prereg": "test-prereg-commit",
        "spec": holdout.frozen_spec(),
        "gate": holdout.gate_from_spec(holdout.frozen_spec()),
        "check": {"passed": False, "coefficient_estimated": False},
        "sources": [],
        "verdict": "INCONCLUSIVE_DATA_PENDING",
        "reason": "test-only source failure",
        "estimate": None,
        "panel": None,
    }
    holdout.record(**state)
    monkeypatch.setattr(holdout, "evaluate", lambda: state)
    files = sorted((tmp_path / "run").iterdir())
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert holdout.check_run()["artifacts_written"] is False
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    assert after == before

    diagnostics_path = tmp_path / "run" / "diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text())
    diagnostics["verdict_label"] = "SUPPORTED"
    diagnostics_path.write_text(json.dumps(diagnostics))
    with pytest.raises(RuntimeError, match="stored_verdict_matches_refit"):
        holdout.check_run()


@pytest.mark.parametrize("stale_path", [
    holdout.PEER_RUNNER_REL,
    "hypotheses/healthcare/trade_openness_physician_density_geographic_holdout_v2.yaml",
    "hypotheses/steelman/trade_openness_secondary_enrollment_geographic_holdout_v2.md",
])
def test_preregistration_guard_requires_full_family_in_head(
    monkeypatch: pytest.MonkeyPatch, stale_path: str,
) -> None:
    def fake_git(*args: str):
        if args[0] == "show":
            relative = args[1].split(":", 1)[1]
            content = (ROOT / relative).read_bytes()
            if relative == stale_path:
                content = b"stale preregistration artifact"
            return subprocess.CompletedProcess(args, 0, stdout=content)
        raise AssertionError("the stale family artifact should stop before git log")

    monkeypatch.setattr(holdout, "git", fake_git)
    with pytest.raises(RuntimeError, match=stale_path):
        holdout.preregistration_commit()
