"""Synthetic guards for the blind WGI/OECD prospective package."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest

RUNNER = Path(__file__).resolve().parents[1] / "scripts/run_wgi_ge_oecd_treatable_mortality_2026.py"
MODULE_SPEC = importlib.util.spec_from_file_location("wgi_ge_oecd_prospective", RUNNER)
study = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC and MODULE_SPEC.loader
MODULE_SPEC.loader.exec_module(study)


def test_key_preflight_projects_no_mortality_values_null_masks_or_statuses(monkeypatch):
    forbidden = set(study.OUTCOME_MEASURED_COLUMNS)
    seen = []

    def fake_read_table(path, *, columns):
        seen.append(tuple(columns))
        assert forbidden.isdisjoint(columns)
        data = {name: [value] for name, value in study.OUTCOME_FILTERS.items()}
        data.update({"REF_AREA": ["GBR"], "period": ["2015"]})
        return pa.Table.from_pydict({name: data[name] for name in columns})

    monkeypatch.setattr(study.pq, "read_table", fake_read_table)
    rows = study.outcome_rows(Path("/synthetic"), measured=False)
    assert seen == [tuple(study.OUTCOME_KEY_COLUMNS)]
    assert rows.to_dict("records") == [{"country_iso3": "GBR", "year": 2014}]


def test_duplicate_selected_outcome_keys_stop_instead_of_averaging(monkeypatch):
    def fake_read_table(path, *, columns):
        data = {name: [value, value] for name, value in study.OUTCOME_FILTERS.items()}
        data.update({"REF_AREA": ["GBR", "GBR"], "period": ["2015", "2015"]})
        return pa.Table.from_pydict({name: data[name] for name in columns})

    monkeypatch.setattr(study.pq, "read_table", fake_read_table)
    with pytest.raises(RuntimeError, match="duplicate selected OECD"):
        study.outcome_rows(Path("/synthetic"), measured=False)


def test_measured_status_value_and_positive_rate_rules():
    base = pd.DataFrame({
        "country_iso3": ["AAA"] * 6, "year": list(range(2000, 2006)),
        "value": [100.0, 80.0, None, -2.0, 70.0, 60.0],
        "Observation value": [100.0, 80.0, None, -2.0, 71.0, 60.0],
        "OBS_STATUS": ["A", "P", "A", "A", "A", ""],
        "OBS_STATUS2": ["", "", "", "", "", "A"],
        "OBS_STATUS3": ["", "", "", "", "", ""],
    })
    clean = study.clean_outcome(base)
    assert clean.year.tolist() == [2000, 2005]
    assert clean.log_mortality.notna().all()


def test_small_sample_and_opposite_sign_do_not_get_credit():
    tiny = pd.DataFrame({"country_iso3": ["AAA", "BBB"], "year": [2000, 2001],
                         "ge": [0.1, 0.2], "log_income": [9.0, 9.2],
                         "log_mortality": [4.0, 3.9]})
    estimate, failures, diagnostics = study.estimate(tiny)
    assert estimate is None
    assert "complete_pair_floor" in failures
    assert "complete_country_floor" in failures
    assert diagnostics["complete_pairs"] == 0
    assert study.classify(-0.05, 0.01) == "SUPPORTED"
    assert study.classify(+0.05, 0.01) == "REFUTED"
    assert study.classify(-0.049, 0.0001) == "PARTIAL"
    assert study.classify(-0.2, 0.01001) == "PARTIAL"


def test_run_checks_committed_source_lock_before_measured_projection(monkeypatch):
    accessed = []

    def fail_lock(source_root):
        raise RuntimeError("source lock not committed")

    def spy_outcome(source_root, *, measured):
        accessed.append(measured)
        raise AssertionError("outcome must not be opened")

    monkeypatch.setattr(study, "committed_lock", fail_lock)
    monkeypatch.setattr(study, "outcome_rows", spy_outcome)
    with pytest.raises(RuntimeError, match="source lock not committed"):
        study.run(Path("/synthetic"))
    assert accessed == []


def test_synthetic_full_panel_estimates_declared_negative_relation():
    import numpy as np

    rng = np.random.default_rng(20261010)
    rows = []
    for country_index in range(35):
        country = f"C{country_index:02d}"
        for year in range(2002, 2018):
            ge = 0.03 * country_index + 0.004 * (year - 2002) + rng.normal(0, 0.18)
            log_income = 8.5 + 0.02 * country_index + 0.018 * (year - 2002) + rng.normal(0, 0.04)
            log_mortality = (5.2 - 0.12 * ge + 0.10 * log_income
                             + 0.007 * country_index - 0.009 * (year - 2002)
                             + rng.normal(0, 0.035))
            rows.append((country, year, ge, log_income, log_mortality))
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "ge", "log_income", "log_mortality"])
    estimate, failures, diagnostic = study.estimate(panel)
    assert failures == []
    assert estimate is not None
    assert diagnostic["complete_pairs"] == 560
    assert estimate["beta_log_points_per_wgi_point"] < -0.05
    assert estimate["verdict"] == "SUPPORTED"


def synthetic_inconclusive_result():
    return {
        "study_id": study.STUDY, "status": "measured_descriptive_calibration",
        "registration_commit": "registration-commit", "source_lock_commit": "lock-commit",
        "key_roster_sha256": study.ROSTER_SHA,
        "source_sha256": {role: source["sha256"] for role, source in study.SOURCES.items()},
        "outcome_selector": study.OUTCOME_FILTERS,
        "selected_outcome_key_rows": 781, "valid_selected_outcome_rows": 300,
        "diagnostics": {"complete_pairs_before_country_floor": 300,
                        "complete_pairs": 280, "complete_countries": 25,
                        "min_complete_years_per_retained_country": 8},
        "failed_gates": ["complete_pair_floor", "complete_country_floor"],
        "estimate": None, "verdict": "INCONCLUSIVE", "limits": study.LIMITATIONS,
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }


def synthetic_source_entries():
    return {role: {**source, "source_url": f"https://example.test/{role}",
                   "methodology_url": f"https://example.test/{role}/method",
                   "license": "test", "fetch_utc": "2026-01-01T00:00:00Z",
                   "start_date": "2000", "end_date": "2023",
                   "frequency": "annual", "units": "test"}
            for role, source in study.SOURCES.items()}


def test_standard_packet_has_nine_hashed_artifacts_and_zero_credit():
    import hashlib
    import io
    import json
    import pyarrow.parquet as pq
    import yaml

    files = study.result_artifacts(synthetic_inconclusive_result(), synthetic_source_entries())
    assert tuple(files) == study.RUN_ARTIFACTS
    diagnostics = json.loads(files["diagnostics.json"])
    assert diagnostics["verdict"] == "INCONCLUSIVE"
    assert diagnostics["correction"]["disposition"] == "descriptive_calibration_only"
    assert diagnostics["correction"]["school_score_credit"] == 0
    manifest = yaml.safe_load(files["manifest.yaml"])
    assert len(manifest["vintages"]) == 3
    assert manifest["missing_series"] == []
    packet = yaml.safe_load(files["evidence_packet.yaml"])
    assert packet["verdict"]["bucket"] == "inconclusive"
    assert packet["credit"]["policy_score_credit"] == 0
    assert {item["path"].split("/")[-1] for item in packet["artifacts"]} == set(study.RUN_ARTIFACTS) - {"evidence_packet.yaml"}
    for item in packet["artifacts"]:
        name = item["path"].split("/")[-1]
        assert item["sha256"] == hashlib.sha256(files[name]).hexdigest()
        assert item["bytes"] == len(files[name])
    coefficient = pq.read_table(io.BytesIO(files["coefficients.parquet"])).to_pandas()
    assert len(coefficient) == 1
    assert coefficient.estimate.isna().all()
    assert coefficient.verdict.tolist() == ["INCONCLUSIVE"]
    compile(files["replication.py"], "replication.py", "exec")
    assert b'"verify"' in files["replication.py"]


def test_exact_replay_works_after_result_commit_and_detects_tamper(monkeypatch, tmp_path):
    import shutil

    source_spec = study.ROOT / study.SPEC
    target_spec = tmp_path / study.SPEC
    target_spec.parent.mkdir(parents=True)
    shutil.copyfile(source_spec, target_spec)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    result = synthetic_inconclusive_result()
    entries = synthetic_source_entries()
    files = study.result_artifacts(result, entries)
    run_dir = tmp_path / study.RESULT_DIR
    run_dir.mkdir(parents=True)
    for name, content in files.items():
        (run_dir / name).write_bytes(content)
    monkeypatch.setattr(study, "committed_lock", lambda _: ("registration-commit", "lock-commit", pd.DataFrame()))
    monkeypatch.setattr(study, "first_addition", lambda _: "result-commit")
    monkeypatch.setattr(study, "is_ancestor", lambda older, newer: True)
    monkeypatch.setattr(study, "frozen_file", lambda path, revision: None)
    monkeypatch.setattr(study, "measured_result", lambda *args: result)
    monkeypatch.setattr(study, "check_sources", lambda _: entries)
    study.verify(tmp_path)
    (run_dir / "diagnostics.json").write_bytes(b"{}\n")
    with pytest.raises(RuntimeError, match="exact replay mismatch: diagnostics.json"):
        study.verify(tmp_path)


def test_verify_requires_measured_result_commit_before_recomputation(monkeypatch):
    calls = []
    monkeypatch.setattr(study, "committed_lock", lambda _: ("registration-commit", "lock-commit", pd.DataFrame()))
    monkeypatch.setattr(study, "first_addition", lambda _: (_ for _ in ()).throw(RuntimeError("result uncommitted")))
    monkeypatch.setattr(study, "measured_result", lambda *args: calls.append("measured"))
    with pytest.raises(RuntimeError, match="result uncommitted"):
        study.verify(Path("/synthetic"))
    assert calls == []
