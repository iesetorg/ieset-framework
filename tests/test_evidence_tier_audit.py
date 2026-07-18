"""Contract tests for the generated public evidence-quality ledger."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_tier_audit_is_fresh():
    result = subprocess.run(
        [sys.executable, "scripts/audit_evidence_tiers.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_public_credit_requires_estimator_floor():
    audit = json.loads(
        (ROOT / "engine" / "evidence_tier_audit.json").read_text(
            encoding="utf-8"
        )
    )
    for record in audit["records"]:
        if record["public_visible"]:
            assert record["estimator_floor"] == "pass"
            assert record["estimator_floor_failures"] == []
            assert record["registration_status"] == "verified"
            assert record["tier"] in {"featured", "calibration"}
        if record["estimator_floor"] == "fail":
            assert record["tier"] == "archive"
            assert "estimator_floor_failed" in record["exclusion_reasons"]


def test_featured_is_stricter_than_public_visibility():
    audit = json.loads(
        (ROOT / "engine" / "evidence_tier_audit.json").read_text(
            encoding="utf-8"
        )
    )
    featured = [
        record for record in audit["records"] if record["tier"] == "featured"
    ]
    calibration = [
        record for record in audit["records"] if record["tier"] == "calibration"
    ]
    assert featured
    assert calibration
    assert all(record["public_visible"] for record in featured)
    assert all(record["evidence_type"] == "causal" for record in featured)
    assert all(record["screening_flags"] == [] for record in featured)
