"""Synthetic contract checks; selected outcome values and statuses are never opened."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "union_density_calibration", ROOT / "scripts/run_union_density_low_education_unemployment_calibration_2026.py")
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_blind_key_roster_and_source_pins(monkeypatch):
    real_read = pd.read_parquet

    def guarded_read(path, *args, **kwargs):
        if str(path).endswith("DSD_LMS_low_education_unemployment_rate@2026-05-05T195457Z.parquet"):
            columns = kwargs.get("columns")
            assert columns is not None
            assert not {"value", "Observation value", "OBS_STATUS", "Observation status"} & set(columns)
        return real_read(path, *args, **kwargs)

    monkeypatch.setattr(m.pd, "read_parquet", guarded_read)
    preflight = m.key_preflight()
    assert preflight["roster_rows"] == 200
    assert preflight["roster_reporter_economies"] == 39
    assert preflight["reporters_with_three_windows"] == 35
    assert not preflight["outcome_values_or_status_read"]
    assert list(preflight["anchor_counts"].values()) == [34, 36, 34, 37, 31, 28]


def test_nonoverlapping_windows_and_exact_threshold():
    rows = m.source_keys()
    assert len(rows) == len(set(rows)) == 200
    by_country = {}
    for country, year in rows:
        by_country.setdefault(country, []).append(year)
    assert all(b-a >= 3 for years in by_country.values()
               for a, b in zip(sorted(years), sorted(years)[1:]))
    spec = yaml.safe_load((ROOT / m.SPEC).read_text())
    assert spec["falsification"]["threshold"] == m.threshold()
    assert spec["covers_claims"] == []
    assert spec["linked_hypotheses"] == []


def test_synthetic_signal_and_verdict():
    rng = np.random.default_rng(23)
    rows = []
    for ci in range(35):
        country = f"C{ci:02d}"
        for yi, year in enumerate(m.ANCHORS):
            union = 10 + ci*.8 + yi*.3 + rng.normal(0, 2.2)
            baseline = 7 + ci*.1 + rng.normal(0, 1)
            income = 9 + ci*.01 + yi*.02 + rng.normal(0, .1)
            outcome = .8*(union/10) + .02*baseline + .03*income + .1*yi + rng.normal(0, .25)
            rows.append({"country_iso3": country, "year": year, "outcome": outcome,
                         "baseline": baseline, "union10": union/10,
                         "union_pp": union, "log_gdp_pc": income})
    frame = pd.DataFrame(rows)
    assert all(m.pre_estimation_gate(frame).values())
    primary, influence = m.estimate(frame)
    assert primary is not None
    assert primary["coefficient"] >= m.MEANINGFUL_BETA
    assert primary["p_value_two_sided"] <= m.ALPHA
    gates = {**m.pre_estimation_gate(frame), "full_rank_and_estimable_uncertainty": True,
             **{name: value is not None and value <= m.FLOOR[name]
                for name, value in influence.items()}}
    assert m.verdict(primary, gates)[0] == "SUPPORTED"
    assert m.verdict({**primary, "coefficient": -.5}, gates)[0] == "REFUTED"
    assert m.verdict({**primary, "p_value_two_sided": .02}, gates)[0] == "PARTIAL"


def test_sparse_complete_cases_do_not_reach_estimator(monkeypatch):
    frame = pd.DataFrame([{"country_iso3": "AAA", "year": 2007,
                           "outcome": 1.0, "baseline": 5.0, "union10": 2.0,
                           "union_pp": 20.0, "log_gdp_pc": 9.0}])
    monkeypatch.setattr(m, "analysis_frame", lambda _rows: (
        frame, {"roster_rows": 1, "invalid_or_missing_outcome_pairs": 0,
                "non_actual_outcome_status_pairs": 0}))

    def forbidden_estimate(_frame):
        raise AssertionError("estimator ran below complete-case floor")

    monkeypatch.setattr(m, "estimate", forbidden_estimate)
    result = m.outcome([("AAA", 2007)], "prereg", "lock", "synthetic-time")
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
    assert result["sample"]["estimator_attempted"] is False
    assert result["gate_checks"]["min_valid_rows"] is False


def test_failed_influence_gate_suppresses_coefficient(monkeypatch):
    rng = np.random.default_rng(5)
    rows = []
    for ci in range(30):
        for yi, year in enumerate(m.ANCHORS):
            density = 10 + ci + rng.normal(0, 3)
            rows.append({"country_iso3": f"C{ci:02d}", "year": year,
                         "outcome": 1.0, "baseline": 5.0,
                         "union10": density/10, "union_pp": density,
                         "log_gdp_pc": 9.0 + rng.normal(0, .1)})
    frame = pd.DataFrame(rows)
    assert all(m.pre_estimation_gate(frame).values())
    monkeypatch.setattr(m, "analysis_frame", lambda _rows: (
        frame, {"roster_rows": len(frame), "invalid_or_missing_outcome_pairs": 0,
                "non_actual_outcome_status_pairs": 0}))
    monkeypatch.setattr(m, "estimate", lambda _frame: (
        {"coefficient": .5, "p_value_two_sided": .001},
        {"max_top_one_percent_partialled_x_share": .5,
         "max_top_country_partialled_x_share": .1}))
    result = m.outcome([], "prereg", "lock", "synthetic-time")
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
    assert result["sample"]["estimator_attempted"] is True
    assert result["gate_checks"]["max_top_one_percent_partialled_x_share"] is False


@pytest.mark.parametrize("failure", ["missing", "uncommitted"])
def test_missing_or_uncommitted_lock_blocks_analysis(monkeypatch, failure):
    if failure == "missing":
        monkeypatch.setattr(m, "first_addition", lambda _relative: (
            (_ for _ in ()).throw(RuntimeError("missing first-addition commit"))))
    else:
        monkeypatch.setattr(m, "first_addition", lambda _relative: "synthetic-lock")
        monkeypatch.setattr(m, "committed_unchanged", lambda _relative, _rev: (
            (_ for _ in ()).throw(RuntimeError("uncommitted frozen file"))))

    def forbidden_analysis(_rows):
        raise AssertionError("selected outcome opened before source lock")

    monkeypatch.setattr(m, "analysis_frame", forbidden_analysis)
    with pytest.raises(RuntimeError, match=("missing first-addition" if failure == "missing"
                                            else "uncommitted frozen file")):
        m.run_or_verify(False)


def test_source_lock_must_descend_from_registration(monkeypatch, tmp_path):
    preflight = {"synthetic": True}
    path = tmp_path / m.LOCK
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(m.lock_payload("prereg-rev", preflight)))
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "first_addition", lambda _relative: "lock-rev")
    monkeypatch.setattr(m, "committed_unchanged", lambda _relative, _rev: None)
    monkeypatch.setattr(m, "registration_commit", lambda: "prereg-rev")
    monkeypatch.setattr(m, "key_preflight", lambda: preflight)
    calls = []

    def unrelated_history(args, **_kwargs):
        calls.append(args)
        return type("Process", (), {"returncode": 1})()

    monkeypatch.setattr(m.subprocess, "run", unrelated_history)
    with pytest.raises(RuntimeError, match="must descend"):
        m.source_lock_commit()
    assert calls == [["git", "merge-base", "--is-ancestor", "prereg-rev", "lock-rev"]]


def test_exact_replay_accepts_match_and_rejects_drift(monkeypatch, tmp_path):
    rows = [("AAA", 2007)]
    raw_roster = b"synthetic-roster\n"
    roster_path = tmp_path / m.ROSTER
    roster_path.parent.mkdir(parents=True)
    roster_path.write_bytes(raw_roster)
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "source_lock_commit", lambda: (
        "lock-rev", {"preregistration_commit": "prereg-rev"}))
    monkeypatch.setattr(m, "source_keys", lambda: rows)
    monkeypatch.setattr(m, "roster_bytes", lambda _rows: raw_roster)
    monkeypatch.setattr(m, "outcome", lambda _rows, _prereg, _lock, stamp: (
        {"hypothesis_id": m.ID, "run_utc": stamp}))
    monkeypatch.setattr(m, "artifact_bytes", lambda result: {
        "diagnostics.json": (json.dumps(result, sort_keys=True)+"\n").encode(),
        "synthetic.txt": b"frozen\n"})
    stamp = "2026-01-01T00:00:00+00:00"
    dest = tmp_path / m.RUN
    dest.mkdir(parents=True)
    for name, raw in m.artifact_bytes({"hypothesis_id": m.ID, "run_utc": stamp}).items():
        (dest / name).write_bytes(raw)
    m.run_or_verify(True)
    (dest / "synthetic.txt").write_bytes(b"drift\n")
    with pytest.raises(RuntimeError, match="exact replay mismatch"):
        m.run_or_verify(True)
