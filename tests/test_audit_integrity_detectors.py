"""Tests for the adversarial-audit integrity detectors (2026-09-03 remediation).

Drives the real shipped detectors in scripts/audit_integrity_detectors.py
against the real diagnostics.json artifacts the 2026-07-31 adversarial audit
cited, so the sentinel / duplicate-hash / unit-mismatch / sample-explosion
defect classes cannot silently regress.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DET = load_script("audit_integrity_detectors")


def load_diag(run_id: str) -> dict:
    return json.loads((ROOT / "engine" / "runs" / run_id / "diagnostics.json").read_text())


# --- X2: sentinel values (audit record B) ---------------------------------- #

def test_sentinel_detector_flags_soviet_impossible_pct_decline():
    diag = load_diag("soviet_union_central_planning_gdp_collapse_1989_1991")
    findings = DET.detect_sentinel_values(diag["metrics"])
    flagged = {f["metric_id"] for f in findings}
    # diagnostics.json:28 — observed 99.99999929185707 on peak_to_trough_pct_decline
    assert "gdp_contraction_peak_to_trough" in flagged
    by_id = {f["metric_id"]: f for f in findings}
    assert by_id["gdp_contraction_peak_to_trough"]["observed_value"] > 99.99


def test_sentinel_detector_flags_greece_scaled_artefacts():
    diag = load_diag("banking_crisis_greece_2010_2018_doom_loop")
    findings = DET.detect_sentinel_values(diag["metrics"])
    flagged = {f["metric_id"] for f in findings}
    # audit claim 15: unemployment 1.43e+03 pct-increase vs pp threshold;
    # government_debt 4.94e+04 max_in_window vs "% of GDP" threshold
    assert "unemployment_peak" in flagged
    assert "government_debt_peak" in flagged


def test_sentinel_detector_clean_on_plausible_pct_stats():
    metrics = [
        {"metric_id": "sane_decline", "observed_value": 30.2,
         "observed_stat_name": "peak_to_trough_pct_decline", "threshold": ">30% decline"},
        {"metric_id": "sane_ratio", "observed_value": 187.0,
         "observed_stat_name": "max_in_window_fallback", "threshold": ">= 175% of GDP"},
        {"metric_id": "no_value", "observed_value": None,
         "observed_stat_name": "complex_threshold", "threshold": ">=2 consecutive years"},
    ]
    assert DET.detect_sentinel_values(metrics) == []


# --- X1: unit typetag mismatch (audit record A) ----------------------------- #

def test_unit_detector_flags_soviet_absolute_thresholds_vs_pct_stats():
    diag = load_diag("soviet_union_central_planning_gdp_collapse_1989_1991")
    mismatches = {
        m["metric_id"]: DET.detect_unit_typetag_mismatch(m)
        for m in diag["metrics"]
    }
    # audit X1: ">5 year decline" scored against an 11.56 percent stat
    assert "years_absolute" in mismatches["life_expectancy_male_collapse"]["threshold_units"]
    # audit X1: ">0.5 decline in TFR" scored against a 98.2 percent stat
    assert "tfr_points" in mismatches["fertility_collapse_tfr"]["threshold_units"]
    # audit X1: ">20 percentage point" poverty threshold vs 6.98 pct-increase stat
    assert "percentage_points" in mismatches["poverty_headcount_surge"]["threshold_units"]


def test_unit_detector_passes_matching_percent_threshold():
    metric = {
        "metric_id": "industrial_output_collapse",
        "observed_value": 56.4,
        "observed_stat_name": "peak_to_trough_pct_decline",
        "threshold": ">40% decline in industrial production index 1990-1998",
    }
    assert DET.detect_unit_typetag_mismatch(metric) is None


# --- X3: duplicate source hashes (audit record C) --------------------------- #

def test_duplicate_hash_detector_flags_soviet_shared_vintages():
    diag = load_diag("soviet_union_central_planning_gdp_collapse_1989_1991")
    findings = DET.detect_duplicate_source_hashes(diag)
    assert findings, "expected shared-hash findings in the Soviet run diagnostics"
    by_metric = {f["metric_id"]: f for f in findings}
    # audit X3: rosstat:demographic_yearbook and human_mortality_database:RUS
    # share sha256 da0c27… — the life-expectancy metric's 3 publishers are
    # served by that single file
    life_exp = by_metric["life_expectancy_male_collapse"]
    assert life_exp["publishers"] == [
        "human_mortality_database:RUS",
        "rosstat:demographic_yearbook",
        "who_gho:life_expectancy",
    ]
    assert life_exp["sha256"] == [
        h for h in life_exp["sha256"] if h.startswith("da0c27")
    ] and len(life_exp["sha256"]) == 1
    # every finding must declare more publishers than distinct files
    assert all(len(f["publishers"]) > len(f["sha256"]) for f in findings)


def test_duplicate_hash_detector_clean_when_publishers_match_files():
    diag = {
        "metrics": [
            {"metric_id": "a", "source": "pub_one:x; pub_two:y",
             "vintage_sha256": ["1" * 64, "2" * 64]},
            {"metric_id": "b", "source": "pub_one:x",
             "vintage_sha256": ["1" * 64]},
        ]
    }
    assert DET.detect_duplicate_source_hashes(diag) == []


# --- X4: sample-scope explosion (audit record D) ---------------------------- #

def test_sample_assertion_flags_gfc_world_panel_count():
    diag = load_diag("banking_crisis_2008_gfc_canonical_multimetric")
    findings = DET.detect_sample_explosion(diag["metrics"])
    flagged = {f["metric_id"]: f for f in findings}
    # audit X4: 254 entities counted against "at least 5 of 9 countries"
    assert "peak_to_trough_real_gdp_decline" in flagged
    assert flagged["peak_to_trough_real_gdp_decline"]["declared_sample_size"] == 9
    assert flagged["peak_to_trough_real_gdp_decline"]["observed_count"] == 254


def test_sample_assertion_passes_restricted_counts():
    diag = load_diag("banking_crisis_asian_financial_crisis_1997_panel")
    findings = DET.detect_sample_explosion(diag["metrics"])
    flagged = {f["metric_id"] for f in findings}
    # the IMF-programme metric was correctly restricted to the named five
    assert "imf_programme_entered" not in flagged
    # while the depreciation count scanned the world (62 vs "of 5")
    assert "nominal_currency_depreciation_peak" in flagged


def test_count_exceeds_declared_sample_pure_assertion():
    assert DET.count_exceeds_declared_sample(254, 9) is True
    assert DET.count_exceeds_declared_sample(5, 9) is False
    assert DET.count_exceeds_declared_sample(9, 9) is False


# --- aggregate scan --------------------------------------------------------- #

def test_scan_diagnostics_aggregates_all_detector_classes_for_soviet_run():
    result = DET.scan_diagnostics(load_diag("soviet_union_central_planning_gdp_collapse_1989_1991"))
    classes = {f["detector"] for f in result["findings"]}
    assert classes == {
        "sentinel_value",
        "unit_typetag_mismatch",
        "duplicate_source_hash",
    }


def test_scan_skips_non_metric_diagnostics_shape():
    assert "skipped" in DET.scan_diagnostics({"verdict": "SUPPORTED", "metrics": []})
