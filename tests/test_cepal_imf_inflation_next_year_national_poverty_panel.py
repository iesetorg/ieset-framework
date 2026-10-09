"""Structural and synthetic-only checks for the frozen CEPAL/IMF registration."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_cepal_imf_inflation_next_year_national_poverty_panel.py"
spec = importlib.util.spec_from_file_location("cepal_imf_runner", RUNNER)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
adapter_path = ROOT / "scripts/verify_cepal_imf_from_narrow_lock.py"
adapter_spec = importlib.util.spec_from_file_location("cepal_imf_narrow_adapter", adapter_path)
assert adapter_spec is not None and adapter_spec.loader is not None
adapter = importlib.util.module_from_spec(adapter_spec)
adapter_spec.loader.exec_module(adapter)


def raw_sources_present():
    return all((ROOT / row["path"]).exists() for row in runner.SOURCES.values())


def test_preflight_projects_dimension_keys_only(monkeypatch):
    if not raw_sources_present():
        pytest.skip("ignored pinned raw files are absent from this checkout")
    original = runner.pd.read_parquet
    projected = []

    def guarded(*args, **kwargs):
        columns = kwargs.get("columns")
        projected.append(columns)
        assert columns is not None
        assert "value" not in columns
        return original(*args, **kwargs)

    monkeypatch.setattr(runner.pd, "read_parquet", guarded)
    monkeypatch.setattr(runner, "manifest_entries", adapter.selected_entries_from_committed_lock)
    gate = runner.structural_preflight()
    assert len(projected) == 3
    assert gate["selected_structural_keys"] == 281
    assert gate["structural_key_sha256"] == runner.EXPECTED_KEY_SHA256
    assert gate["measured_values_or_null_masks_read"] is False


def test_narrow_lock_contains_only_selected_source_metadata(monkeypatch):
    if not raw_sources_present():
        pytest.skip("ignored pinned raw files are absent from this checkout")
    monkeypatch.setattr(runner, "manifest_entries", adapter.selected_entries_from_committed_lock)
    lock = runner.expected_source_lock()
    assert set(lock["selected_source_entries"]) == set(runner.SOURCES)
    assert lock["actual_year_status"]["all_selected_exposure_years_actual"] is True
    content = json.dumps(lock)
    assert str(Path.home()) not in content
    assert "raw_path" not in content
    assert "tesouro_br" not in content


def test_result_replays_without_broad_manifest():
    if not raw_sources_present():
        pytest.skip("ignored pinned raw files are absent from this checkout")
    assert not (ROOT / runner.SOURCE_MANIFEST).exists()
    assert adapter.verify()["verified"] is True


def test_classification_has_materiality_precision_and_stability_gates():
    sample = {
        "treatment_coefficient_pp": 0.6,
        "two_sided_t_p_value": 0.01,
        "leave_one_out_positive_share": 13 / 14,
        "leave_one_out_negative_share": 1 / 14,
    }
    assert runner.classify(sample)[0] == "SUPPORTED"
    assert runner.classify({**sample, "treatment_coefficient_pp": 0.49})[0] == "PARTIAL"
    assert runner.classify({**sample, "two_sided_t_p_value": 0.025})[0] == "PARTIAL"
    assert runner.classify({**sample, "leave_one_out_positive_share": 11 / 14})[0] == "PARTIAL"
    negative = {
        **sample,
        "treatment_coefficient_pp": -0.6,
        "leave_one_out_positive_share": 1 / 14,
        "leave_one_out_negative_share": 13 / 14,
    }
    assert runner.classify(negative)[0] == "REFUTED"
