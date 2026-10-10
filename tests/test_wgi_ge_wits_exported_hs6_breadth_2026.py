"""Synthetic guard, source-projection, inference, and exact-packet tests."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "wgi_wits_runner", ROOT / "scripts/run_wgi_ge_wits_exported_hs6_breadth_2026.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_registered_spec_matches_guard_and_roster():
    spec = yaml.safe_load((ROOT / runner.SPEC).read_text())
    assert spec["falsification"]["threshold"] == runner.threshold()
    roster = runner.load_roster()
    assert spec["sample"]["countries"] == sorted({country for country, _ in roster})
    assert len(roster) == runner.KEY_ROWS


def test_wits_preflight_projects_only_dimensions_and_keys(monkeypatch, tmp_path):
    """The outcome's value and null mask cannot enter source-only preflight."""
    columns_seen = []
    selected = {**runner.WITS_SELECTOR, "country_iso3": "GBR", "year": 2010}
    monkeypatch.setattr(runner.pq, "ParquetFile", lambda _: SimpleNamespace(
        metadata=SimpleNamespace(num_rows=5308),
        schema_arrow=SimpleNamespace(names=runner.WITS_KEY_COLUMNS + ["value"]),
    ))

    def read_parquet(_path, *, columns):
        columns_seen.extend(columns)
        return pd.DataFrame([selected])[columns]

    monkeypatch.setattr(runner.pd, "read_parquet", read_parquet)
    assert runner.selected_wits_keys(tmp_path) == {("GBR", 2010)}
    assert columns_seen == runner.WITS_KEY_COLUMNS
    assert "value" not in columns_seen


def test_numeric_wits_contract_is_strict():
    assert runner.valid_count(0) == 0
    assert runner.valid_count(4125) == 4125
    assert runner.valid_count(-1) is None
    assert runner.valid_count(1.5) is None
    assert runner.valid_count(float("nan")) is None
    assert runner.valid_count(None) is None


def test_uncommitted_registration_stops_before_outcome_access(monkeypatch):
    monkeypatch.setattr(runner, "check_sources", lambda _: {})
    monkeypatch.setattr(runner, "preflight", lambda _: {})
    monkeypatch.setattr(runner, "registration_commit", lambda: (_ for _ in ()).throw(RuntimeError("not registered")))
    monkeypatch.setattr(runner, "measured_panel", lambda _: pytest.fail("outcome opened before registration"))
    monkeypatch.setattr(sys, "argv", ["runner", "--run"])
    with pytest.raises(RuntimeError, match="not registered"):
        runner.main()


def test_failed_complete_case_floor_stays_inconclusive():
    gate = {"valid_rows": 0, "valid_countries": 0, "improvement_rows": 0,
            "improvement_countries": 0, "deterioration_rows": 0,
            "deterioration_countries": 0}
    result = runner.estimate(pd.DataFrame(), gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None


def synthetic_panel(seed=20261010):
    rng = np.random.default_rng(seed)
    reporters = [f"R{i:03d}" for i in range(120)]
    years = range(2004, 2016)
    rows = []
    reporter_effect = {reporter: rng.normal(0, 0.02) for reporter in reporters}
    year_effect = {year: rng.normal(0, 0.015) for year in years}
    for reporter in reporters:
        for year in years:
            x = rng.normal(0.025, 0.20)
            baseline = rng.normal(7.5, 0.3)
            prior = rng.normal(0, 0.08)
            log_gdp = rng.normal(9.5, 0.5)
            gdp_change = rng.normal(0.035, 0.06)
            y = (0.25 * x + 0.04 * prior + 0.01 * log_gdp + reporter_effect[reporter]
                 + year_effect[year] + rng.normal(0, 0.10))
            rows.append({"country_iso3": reporter, "year": year, "delta_wgi": x,
                         "improvement": int(x >= runner.MATERIAL),
                         "deterioration": int(x <= -runner.MATERIAL),
                         "baseline_breadth": baseline, "prior_breadth_change": prior,
                         "log_gdp_pc": log_gdp, "prior_gdp_change": gdp_change,
                         "forward_change": y})
    panel = pd.DataFrame(rows)
    gate = {"valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
            "improvement_rows": int(panel.improvement.sum()),
            "improvement_countries": panel.loc[panel.improvement.eq(1), "country_iso3"].nunique(),
            "deterioration_rows": int(panel.deterioration.sum()),
            "deterioration_countries": panel.loc[panel.deterioration.eq(1), "country_iso3"].nunique()}
    return panel, gate


def test_synthetic_forward_effect_respects_frozen_estimator():
    panel, gate = synthetic_panel()
    result = runner.estimate(panel, gate)
    assert result["verdict"] == "SUPPORTED"
    assert result["primary"]["beta_log1p_breadth_per_wgi_point"] > 0.10
    assert result["primary"]["p_value_two_sided"] <= 0.01
    assert result["gate"]["residual_treatment_shares"]["top_one_percent_rows"] <= 0.30


def test_standard_packet_exact_replay_detects_tamper(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    (tmp_path / runner.SPEC).parent.mkdir(parents=True)
    (tmp_path / runner.SPEC).write_text("hypothesis_id: synthetic\n")
    (tmp_path / runner.SUMMARY).parent.mkdir(parents=True)
    gate = {"valid_rows": 1200, "valid_countries": 100, "improvement_rows": 210,
            "improvement_countries": 76, "deterioration_rows": 105,
            "deterioration_countries": 51}
    primary = {"beta_log1p_breadth_per_wgi_point": 0.2, "std_error": 0.04,
               "p_value_two_sided": 0.001, "confidence_level": 0.99,
               "confidence_interval": [0.09, 0.31], "n_rows": 1200,
               "n_reporters": 100, "df_inference": 99, "model_rank": 120,
               "method": "synthetic"}
    result = {"verdict": "SUPPORTED", "reason": "synthetic test", "gate": gate, "primary": primary}
    runner.write_artifacts(result, "registration", "source-lock")
    folder = tmp_path / runner.RESULT_DIR
    assert {"evidence_packet.yaml", "diagnostics.json", "manifest.yaml", "hypothesis.yaml",
            "replication.py", "result_card.md", "chart_data.json", "coefficients.parquet"} <= {
        path.name for path in folder.iterdir()
    }
    runner.verify_artifacts(result, "registration", "source-lock")
    chart_path = folder / "chart_data.json"
    chart = json.loads(chart_path.read_text())
    chart["verdict"] = "REFUTED"
    chart_path.write_text(json.dumps(chart))
    with pytest.raises(AssertionError, match="chart"):
        runner.verify_artifacts(result, "registration", "source-lock")
