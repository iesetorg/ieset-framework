"""Focused synthetic and blind-access tests for the CEPII/WDI registration."""
from __future__ import annotations

import importlib.util
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_cepii_new_fta_partners_manufactures_share_forward_2026.py"
spec = importlib.util.spec_from_file_location("cepii_manufactures", SCRIPT)
assert spec is not None and spec.loader is not None
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def synthetic_panel(event_effect: float) -> tuple[pd.DataFrame, dict]:
    rows = []
    for country in range(75):
        for year in range(1995, 2015):
            event = int((country + 3 * (year - 1995)) % 7 == 0)
            baseline = 38 + 0.13 * country + 0.17 * (year - 1995) \
                + 1.4 * math.sin(country * 0.71 + year * 0.32)
            noise = 0.21 * math.sin(country * 2.31 + year * 0.81)
            rows.append({
                "country_iso3": f"C{country:02d}", "year": year,
                "new_fta_partner_count": event, "event": event,
                "baseline_share": baseline,
                "share_forward_change": event_effect * event - 0.06 * baseline
                + 0.009 * country + 0.028 * (year - 1995) + noise,
            })
    panel = pd.DataFrame(rows)
    events, controls = panel.loc[panel.event.eq(1)], panel.loc[panel.event.eq(0)]
    gate = {
        "roster_rows": len(panel), "dropped_missing_or_invalid_endpoint_pairs": 0,
        "complete_pairs_before_five_year_country_floor": len(panel),
        "dropped_by_five_year_country_floor": 0,
        "valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
        "event_rows": len(events), "event_countries": events.country_iso3.nunique(),
        "event_years": events.year.nunique(),
        "control_rows": len(controls), "control_countries": controls.country_iso3.nunique(),
        "outcome_values_read_after_lock": True, "outcome_status_read": False,
    }
    return panel, gate


def test_frozen_spec_matches_runner_contract_and_roster() -> None:
    actual_spec = yaml.safe_load((ROOT / study.SPEC).read_text())
    assert actual_spec["falsification"]["threshold"] == study.threshold()
    rows = study.load_roster()
    assert len(rows) == 5028
    assert sum(event for _, _, _, event in rows) == 1013
    assert all(event == int(new_count >= 1) for _, _, new_count, event in rows)


def test_synthetic_directional_verdicts_and_inconclusive_floor() -> None:
    positive, positive_gate = synthetic_panel(2.0)
    supported = study.estimate(positive, positive_gate)
    assert supported["verdict"] == "SUPPORTED"
    assert supported["primary"]["coefficient"] >= study.MEANINGFUL_BETA
    assert supported["primary"]["p_value_two_sided"] <= study.P_MAX
    assert supported["gate"]["partialled_event_full_model"]["top_country_share"] <= study.MAX_COUNTRY

    negative, negative_gate = synthetic_panel(-2.0)
    refuted = study.estimate(negative, negative_gate)
    assert refuted["verdict"] == "REFUTED"
    assert refuted["primary"]["coefficient"] <= -study.MEANINGFUL_BETA

    failed = dict(positive_gate)
    failed["event_years"] = study.MIN_EVENT_YEARS - 1
    inconclusive = study.estimate(positive, failed)
    assert inconclusive["verdict"] == "INCONCLUSIVE"
    assert inconclusive["primary"] is None


def test_preflight_projects_only_wdi_selector_and_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome_path = ROOT / study.SOURCES["outcome"]["path"]
    treatment_path = ROOT / study.SOURCES["treatment"]["path"]
    if not outcome_path.exists() or not treatment_path.exists():
        pytest.skip("pinned local data files unavailable in this checkout")
    real_read = study.pd.read_parquet
    seen = []

    def checked_read(path: Path, *args, **kwargs):
        if Path(path) == outcome_path:
            columns = kwargs.get("columns")
            assert columns is not None
            assert set(columns) == {"country_iso3", "indicator_id", "year"}
            assert not {"value", "obs_status"} & set(columns)
            seen.append(tuple(columns))
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(study.pd, "read_parquet", checked_read)
    treatment, keys = study.source_keys()
    assert len(treatment) == 16366
    assert len(keys) == 14190
    assert len(seen) == 1


def test_full_artifact_replay_rejects_nonprimary_tampering(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    panel, gate = synthetic_panel(2.0)
    result = study.estimate(panel, gate)
    monkeypatch.setattr(study, "ROOT", tmp_path)
    spec_path = tmp_path / study.SPEC
    spec_path.parent.mkdir(parents=True)
    spec_path.write_text("synthetic frozen spec\n")
    (tmp_path / study.SUMMARY).parent.mkdir(parents=True)
    registration, lock_commit = "a" * 40, "b" * 40
    study.write_artifacts(result, registration, lock_commit)
    study.verify_artifacts(result, registration, lock_commit)

    chart_path = tmp_path / study.RUN_DIR / "chart_data.json"
    chart = json.loads(chart_path.read_text())
    chart["family_id"] = "tampered"
    chart_path.write_text(json.dumps(chart) + "\n")
    with pytest.raises(AssertionError, match="chart_data"):
        study.verify_artifacts(result, registration, lock_commit)

    chart_path.write_text(json.dumps(study.artifacts(result, registration, lock_commit,
                                                      json.loads((tmp_path / study.RUN_DIR /
                                                                  "diagnostics.json").read_text())["run_utc"])["chart"],
                                     indent=2) + "\n")
    coefficient_path = tmp_path / study.RUN_DIR / "coefficients.parquet"
    coefficients = pd.read_parquet(coefficient_path)
    coefficients.loc[0, "coefficient"] += 0.25
    coefficients.to_parquet(coefficient_path, index=False)
    with pytest.raises(AssertionError, match="coefficients"):
        study.verify_artifacts(result, registration, lock_commit)


def test_artifact_replay_rejects_truncated_lists() -> None:
    with pytest.raises(AssertionError, match="list length differs"):
        study.replay_equal([1], [1, 2], "truncated")


def test_registration_precedes_selected_outcome_access() -> None:
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", study.SPEC],
                             cwd=ROOT, capture_output=True).returncode == 0
    if tracked:
        assert len(study.registration_commit()) == 40
    else:
        with pytest.raises(RuntimeError, match="first-addition commit"):
            study.registration_commit()
