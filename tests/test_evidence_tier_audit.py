"""Contract tests for the generated public evidence-quality ledger."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_evidence_tiers as evidence_tiers  # noqa: E402


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


def test_pcw100_public_calibration_has_explicit_zero_school_credit():
    path = ROOT / "hypotheses" / "distribution" / "pcw100_us_mw_bite_ratio_p10_wage.yaml"
    assert path.exists()
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["audit_disposition"] == "rescoped_descriptive"
    assert record["public_visible"] is True
    assert record["tier"] == "calibration"
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert record["exclusion_reasons"] == []


def test_rescoped_screen_stays_inspectable_with_score_cap():
    path = ROOT / "hypotheses" / "trade" / "pcw100_global_efw_trade_freedom_gdp_growth.yaml"
    assert path.exists()
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["audit_disposition"] == "rescoped_screen_positive"
    assert record["public_visible"] is True
    assert record["tier"] == "calibration"
    assert record["scoreboard_weight_cap"] == 0.25


def test_live_detector_finding_holds_record():
    path = ROOT / "hypotheses" / "growth" / "soviet_union_central_planning_gdp_collapse_1989_1991.yaml"
    assert path.exists()
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert "integrity_detector_flagged" in record["exclusion_reasons"]
    assert record["public_visible"] is False


def test_incomplete_secondary_endpoint_caps_causal_run_at_calibration():
    path = ROOT / "hypotheses" / "growth" / "latam_extra_inflation_targeting_diff_in_diff_1999_2024.yaml"
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["registration_status"] == "verified"
    assert record["public_visible"] is True
    assert record["run_tier_recommendation"] == "calibration"
    assert record["tier"] == "calibration"


def test_explicit_zero_credit_signal_holds_public_school_scoring():
    assert evidence_tiers.school_score_eligible_for_public_run(True, {"school_score_credit": 0}) is False
    assert evidence_tiers.school_score_eligible_for_public_run(True, {"school_score_eligible": False}) is False
    assert evidence_tiers.school_score_eligible_for_public_run(True, {}) is True
    assert evidence_tiers.school_score_eligible_for_public_run(False, {}) is False


def test_frozen_geographic_holdouts_have_external_zero_school_credit():
    exclusions = evidence_tiers.load_school_score_exclusions()
    expected = {
        "government_consumption_private_consumption_geographic_holdout_v2",
        "hightech_export_share_income_growth_geographic_holdout_v2",
        "real_income_life_expectancy_geographic_holdout_v2",
        "regulatory_quality_private_consumption_geographic_holdout_v2",
        "regulatory_quality_tertiary_enrollment_geographic_holdout_v2",
    }
    assert expected <= set(exclusions)
    audit = evidence_tiers.build()
    records = {row["hypothesis_id"]: row for row in audit["records"]}
    for hypothesis_id in expected:
        record = records[hypothesis_id]
        assert record["public_visible"] is True
        assert record["tier"] == "calibration"
        assert record["school_score_eligible"] is False
        assert record["scoreboard_weight_cap"] == 0.0
        assert record["school_score_exclusion_reason"] == exclusions[hypothesis_id]
        spec_path = ROOT / evidence_tiers.registration_rows()[hypothesis_id]["path"]
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        assert spec["covers_claims"] == []
        assert spec["linked_hypotheses"] == []


def test_epl_duration_holdout_is_public_calibration_with_zero_school_credit():
    hypothesis_id = "oecd_epl_2023_eurostat_longterm_unemployment_2025_v2"
    path = ROOT / "hypotheses" / "labour" / f"{hypothesis_id}.yaml"
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["registration_status"] == "verified"
    assert record["verdict_bucket"] == "partial"
    assert record["public_visible"] is True
    assert record["tier"] == "calibration"
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert record["exclusion_reasons"] == []


def test_school_score_exclusion_registry_fails_closed(tmp_path):
    path = tmp_path / "exclusions.json"
    with pytest.raises(FileNotFoundError):
        evidence_tiers.load_school_score_exclusions(path)
    path.write_text(json.dumps({
        "schema": "ieset-school-score-exclusions-v1",
        "exclusions": [
            {"hypothesis_id": "same_id", "reason": "calibration only"},
            {"hypothesis_id": "same_id", "reason": "calibration only"},
        ],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        evidence_tiers.load_school_score_exclusions(path)


def test_source_locked_nested_result_needs_immutable_ordered_custody():
    hypothesis_id = "jst_1929_1933_advanced_trade_openness_drop_v2"
    run_dir = ROOT / "engine" / "runs" / hypothesis_id
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text())
    registration = evidence_tiers.registration_rows()[hypothesis_id]
    assert evidence_tiers.immutable_source_locked_nested_verdict(
        diagnostics, hypothesis_id, run_dir, registration
    ) == "SUPPORTED"
    assert evidence_tiers.immutable_source_locked_nested_verdict(
        diagnostics, hypothesis_id, run_dir, {**registration, "status": "legacy_same_commit"}
    ) == ""
    assert evidence_tiers.immutable_source_locked_nested_verdict(
        {**diagnostics, "source_sha256": "0" * 64}, hypothesis_id, run_dir, registration
    ) == ""
    assert evidence_tiers.immutable_source_locked_nested_verdict(
        {**diagnostics, "source_lock_commit": "0" * 40}, hypothesis_id, run_dir, registration
    ) == ""


def test_jst_trade_is_public_descriptive_calibration_with_zero_school_credit():
    hypothesis_id = "jst_1929_1933_advanced_trade_openness_drop_v2"
    path = ROOT / "hypotheses" / "trade" / f"{hypothesis_id}.yaml"
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["registration_status"] == "verified"
    assert record["verdict_bucket"] == "supported"
    assert record["public_visible"] is True
    assert record["tier"] == "calibration"
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert record["exclusion_reasons"] == []
    old_path = ROOT / "hypotheses" / "trade" / "trade_lib_smoot_hawley_1930_historical.yaml"
    old_record = evidence_tiers.build_record(old_path, evidence_tiers.registration_rows())
    assert old_record["public_visible"] is False
    assert old_record["tier"] == "archive"


def test_acs_teen_non_alabama_v2_is_partial_zero_school_calibration():
    hypothesis_id = "us_state_minimum_wage_bite_teen_employment_non_alabama_2026_v2"
    path = ROOT / "hypotheses" / "labour" / f"{hypothesis_id}.yaml"
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["registration_status"] == "verified"
    assert record["verdict_bucket"] == "partial"
    assert record["public_visible"] is True
    assert record["tier"] == "calibration"
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert record["exclusion_reasons"] == []


def test_original_acs_teen_roster_stays_archived_after_prelock_peek():
    hypothesis_id = "us_state_minimum_wage_bite_teen_employment_2026"
    path = ROOT / "hypotheses" / "labour" / f"{hypothesis_id}.yaml"
    record = evidence_tiers.build_record(path, evidence_tiers.registration_rows())
    assert record["registration_status"] == "registered_no_run"
    assert record["public_visible"] is False
    assert record["tier"] == "archive"
    assert record["school_score_eligible"] is False
    assert record["scoreboard_weight_cap"] == 0.0
    assert "external_integrity_quarantine" in record["exclusion_reasons"]
