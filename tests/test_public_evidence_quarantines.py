"""Public evidence holds for saved panel runs with invalid or incomplete outcomes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_evidence_tiers as evidence_tiers  # noqa: E402


QUARANTINED = {
    "minimum_wage_youth_unemployment_tradeoff",
    "unemployment_benefit_generosity_employment_drag",
    "workfare_conditionality_employment_effect",
    "tariff_protection_duration_growth_drag",
}


def test_dimension_or_scope_invalid_runs_are_archived_without_school_credit():
    quarantines = evidence_tiers.load_public_evidence_quarantines()
    assert QUARANTINED <= set(quarantines)
    records = {row["hypothesis_id"]: row for row in evidence_tiers.build()["records"]}
    for hypothesis_id in QUARANTINED:
        record = records[hypothesis_id]
        assert record["registration_status"] == "verified"
        assert record["verdict_bucket"] == "partial"
        assert record["tier"] == "archive"
        assert record["public_visible"] is False
        assert record["school_score_eligible"] is False
        assert record["scoreboard_weight_cap"] == 0.0
        assert "external_integrity_quarantine" in record["exclusion_reasons"]
        assert record["public_evidence_quarantine_reason"] == quarantines[hypothesis_id]


def test_public_evidence_quarantine_registry_fails_closed(tmp_path):
    path = tmp_path / "quarantines.json"
    with pytest.raises(FileNotFoundError):
        evidence_tiers.load_public_evidence_quarantines(path)
    path.write_text(json.dumps({"schema": "wrong", "quarantines": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        evidence_tiers.load_public_evidence_quarantines(path)
    path.write_text(json.dumps({
        "schema": "ieset-public-evidence-quarantines-v1",
        "quarantines": [
            {"hypothesis_id": "same_id", "reason": "bad measurement"},
            {"hypothesis_id": "same_id", "reason": "bad measurement"},
        ],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        evidence_tiers.load_public_evidence_quarantines(path)


def test_legacy_duration_source_mismatch_stays_quarantined():
    hypothesis_id = "labour_market_flexibility_unemployment_duration"
    quarantines = evidence_tiers.load_public_evidence_quarantines()
    assert hypothesis_id in quarantines
    record = next(row for row in evidence_tiers.build()["records"] if row["hypothesis_id"] == hypothesis_id)
    assert record["registration_status"] == "legacy_same_commit"
    assert record["tier"] == "archive"
    assert record["public_visible"] is False
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert "external_integrity_quarantine" in record["exclusion_reasons"]
    assert record["public_evidence_quarantine_reason"] == quarantines[hypothesis_id]
