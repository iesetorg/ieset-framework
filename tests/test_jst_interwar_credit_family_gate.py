"""A chronology-correct result still archives when its original spec was invalid."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_evidence_tiers


def registration(hid: str, topic: str) -> dict[str, str]:
    run_dir = ROOT / "engine" / "runs" / hid
    diag = json.loads((run_dir / "diagnostics.json").read_text())
    relative = (run_dir / "diagnostics.json").relative_to(ROOT).as_posix()
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    commits = proc.stdout.splitlines()
    assert len(commits) == 1
    return {
        "status": "verified",
        "path": f"hypotheses/{topic}/{hid}.yaml",
        "spec_commit": diag["registration_commit"],
        "run_first_commit": commits[0],
    }


def nested_verdict(hid: str, topic: str) -> str:
    run_dir = ROOT / "engine" / "runs" / hid
    diag = json.loads((run_dir / "diagnostics.json").read_text())
    return audit_evidence_tiers.immutable_source_locked_nested_verdict(
        diag, hid, run_dir, registration(hid, topic),
    )


def test_original_invalid_spec_cannot_be_public() -> None:
    hid = "jst_1929_credit_intensity_real_gdp_pc_loss_v2"
    spec_rel = f"hypotheses/growth/{hid}.yaml"
    commit = registration(hid, "growth")["spec_commit"]
    frozen = subprocess.run(
        ["git", "show", f"{commit}:{spec_rel}"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    schema = json.loads(subprocess.run(
        ["git", "show", f"{commit}:schemas/hypothesis.schema.json"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout)
    errors = list(Draft202012Validator(schema).iter_errors(yaml.safe_load(frozen)))
    assert len(errors) == 1
    assert list(errors[0].absolute_path) == ["sample", "temporal_structure"]
    # Supply the original bytes as the current spec for this call. This
    # bypasses the later metadata-mutation guard and isolates the original
    # schema gate as the reason for the empty public verdict.
    original_read = Path.read_bytes
    def original_spec_bytes(path: Path) -> bytes:
        if path == ROOT / spec_rel:
            return frozen
        return original_read(path)
    with patch.object(Path, "read_bytes", original_spec_bytes):
        assert nested_verdict(hid, "growth") == ""


def test_later_schema_relaxation_cannot_restore_public_credit() -> None:
    hid = "jst_1929_credit_intensity_real_gdp_pc_loss_v2"
    spec_rel = f"hypotheses/growth/{hid}.yaml"
    commit = registration(hid, "growth")["spec_commit"]
    frozen = subprocess.run(
        ["git", "show", f"{commit}:{spec_rel}"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    current_schema_path = ROOT / "schemas/hypothesis.schema.json"
    future_schema = json.loads(subprocess.run(
        ["git", "show", f"{commit}:schemas/hypothesis.schema.json"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout)
    allowed = future_schema["properties"]["sample"]["properties"]["temporal_structure"]["enum"]
    if "cross_section" not in allowed:
        allowed.append("cross_section")
    assert Draft202012Validator(future_schema).is_valid(yaml.safe_load(frozen))

    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text
    def first_spec_bytes(path: Path) -> bytes:
        if path == ROOT / spec_rel:
            return frozen
        if path == current_schema_path:
            return json.dumps(future_schema).encode()
        return original_read_bytes(path)
    def relaxed_schema_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == current_schema_path:
            return json.dumps(future_schema)
        return original_read_text(path, *args, **kwargs)
    with patch.object(Path, "read_bytes", first_spec_bytes), patch.object(
        Path, "read_text", relaxed_schema_text,
    ):
        assert nested_verdict(hid, "growth") == ""


def test_missing_historical_schema_fails_closed() -> None:
    hid = "jst_1929_credit_intensity_real_gdp_pc_loss_v2"
    frozen_registration = registration(hid, "growth")
    missing = ["git", "show", f"{frozen_registration['spec_commit']}:schemas/hypothesis.schema.json"]
    real_run = subprocess.run

    def missing_schema(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        if args == missing:
            return subprocess.CompletedProcess(args, 128, stdout=b"", stderr=b"missing")
        return real_run(args, **kwargs)

    with patch.object(audit_evidence_tiers.subprocess, "run", missing_schema):
        assert not audit_evidence_tiers.original_registration_schema_valid(frozen_registration)


def test_valid_single_source_locked_result_remains_public() -> None:
    hid = "jst_1929_1933_advanced_trade_openness_drop_v2"
    assert nested_verdict(hid, "trade") == "SUPPORTED"


def test_frozen_runner_rejects_post_result_spec_change() -> None:
    proc = subprocess.run(
        ["python3", "scripts/run_jst_interwar_credit_severity_2026.py", "verify"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode != 0
    assert "frozen registration changed after first commit" in proc.stderr
