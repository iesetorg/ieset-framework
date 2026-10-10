"""Synthetic tests for the prospective two-case placeholder replacement family.

These tests never open either selected outcome value or outcome status column.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "placeholder_replacement", ROOT / "scripts/run_placeholder_redesign_two_case_2026.py")
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def test_source_and_blind_key_roster_contract():
    audit = m.key_preflight()
    assert audit["tax"]["roster_rows"] == 2810
    assert audit["tax"]["roster_countries"] == 141
    assert audit["epl"]["roster_rows"] == 89
    assert audit["epl"]["roster_countries"] == 42
    assert not audit["tax"]["outcome_values_or_status_read"]
    assert not audit["epl"]["outcome_values_or_status_read"]


def test_recession_roster_has_no_overlapping_within_country_events():
    rows = m.source_keys()["epl"]
    assert len(rows) == len(set(rows))
    by_country: dict[str, list[int]] = {}
    for c, y in rows:
        by_country.setdefault(c, []).append(y)
    assert all(b-a >= 3 for years in by_country.values()
               for a, b in zip(sorted(years), sorted(years)[1:]))
    assert sum(len(v) >= 2 for v in by_country.values()) == 31
    assert sum(y == 2009 for _, y in rows) == 31
    assert sum(y == 2020 for _, y in rows) == 36


def test_blank_wdi_status_rule():
    assert m.blank_status(None)
    assert m.blank_status(float("nan"))
    assert m.blank_status("  ")
    assert not m.blank_status("P")


def test_frozen_two_test_correction_and_verdict_logic():
    assert m.FAMILY_ALPHA == .01
    assert m.P_MAX == .005
    gates = {"sample": True, "influence": True, "estimator": True}
    assert m.classify_verdict("tax", {"coefficient": .6, "p_value_two_sided": .004}, gates)[0] == "SUPPORTED"
    assert m.classify_verdict("tax", {"coefficient": -.6, "p_value_two_sided": .004}, gates)[0] == "REFUTED"
    assert m.classify_verdict("tax", {"coefficient": .6, "p_value_two_sided": .006}, gates)[0] == "PARTIAL"
    assert m.classify_verdict("tax", {"coefficient": .3, "p_value_two_sided": .001}, gates)[0] == "PARTIAL"
    assert m.classify_verdict("epl", {"coefficient": -.8, "p_value_two_sided": .004}, gates)[0] == "SUPPORTED"
    assert m.classify_verdict("epl", {"coefficient": +.8, "p_value_two_sided": .004}, gates)[0] == "REFUTED"
    assert m.classify_verdict("epl", {"coefficient": -.8, "p_value_two_sided": .004}, {"floor": False})[0] == "INCONCLUSIVE"


def test_private_investment_estimator_recovers_synthetic_signal():
    rng = np.random.default_rng(7)
    rows = []
    for ci in range(40):
        country = f"C{ci:02d}"
        for year in range(2001, 2010):
            cut = int((ci + 3*year) % 7 in (0, 1))
            hike = int((ci + year) % 11 == 0 and not cut)
            baseline = 10 + .25*ci + .1*(year-2001) + rng.normal(0, .2)
            outcome = .9*cut - .2*hike + .03*baseline + .1*(year-2001) + rng.normal(0, .4)
            rows.append({"country_iso3": country, "year": year, "outcome": outcome,
                         "baseline": baseline, "cut": cut, "hike": hike,
                         "stable": int(not cut and not hike), "tax_delta": -1.5 if cut else (1.5 if hike else 0)})
    frame = pd.DataFrame(rows)
    estimate, concentration = m.estimate("tax", frame)
    assert estimate is not None
    assert estimate["coefficient"] > .5
    assert estimate["p_value_two_sided"] < m.P_MAX
    assert concentration["max_top_country_partialled_x_share"] is not None
    gates = m.sample_gate("tax", frame, concentration)
    assert gates["min_cut_rows"]
    assert gates["min_cut_countries"]
    assert gates["min_stable_rows"]


def test_employment_recovery_estimator_recovers_synthetic_signal():
    rng = np.random.default_rng(11)
    rows = []
    for ci in range(40):
        country = f"C{ci:02d}"
        base_epl = .3 + (ci % 20)*.18
        for year in (2009, 2012, 2020):
            epl = base_epl + .04*(year-2009)/3
            baseline = 65 + .2*ci + rng.normal(0, .5)
            shock = -1 - (ci % 5)*.8 - (year == 2020)*1.2
            outcome = -1.2*epl + .03*baseline + .2*shock + .4*(year == 2020) + rng.normal(0, .35)
            rows.append({"country_iso3": country, "year": year, "outcome": outcome,
                         "baseline": baseline, "epl": epl, "gdp_shock": shock})
    frame = pd.DataFrame(rows)
    estimate, concentration = m.estimate("epl", frame)
    assert estimate is not None
    assert estimate["coefficient"] < -.75
    assert estimate["p_value_two_sided"] < m.P_MAX
    gates = m.sample_gate("epl", frame, concentration)
    assert gates["min_valid_rows"]
    assert gates["min_countries_with_two_nonoverlapping_events"]
    assert gates["min_2009_events"] and gates["min_2020_events"]


def test_rank_failure_is_inconclusive():
    rows = []
    for ci in range(32):
        for year in (2009, 2012, 2020):
            rows.append({"country_iso3": f"C{ci:02d}", "year": year,
                         "outcome": float(ci), "baseline": float(ci),
                         "epl": 1.0, "gdp_shock": -2.0})
    fit, _ = m.estimate("epl", pd.DataFrame(rows))
    assert fit is None
    assert m.classify_verdict("epl", fit, {"rank": False})[0] == "INCONCLUSIVE"


@pytest.mark.parametrize("key", ["tax", "epl"])
def test_sparse_outcome_stops_before_estimator(monkeypatch, key):
    row = {"country_iso3": "AAA", "year": 2009, "outcome": 1.0, "baseline": 2.0}
    if key == "tax":
        row.update(cut=1, hike=0, stable=0, tax_delta=-1.5)
    else:
        row.update(epl=2.0, gdp_shock=-2.0)
    monkeypatch.setattr(m, "analysis_frame", lambda _key, _roster: (
        pd.DataFrame([row]), {"roster_rows": 1, "invalid_or_missing_outcome_pairs": 0,
                              "non_actual_outcome_status_pairs": 0}))

    def forbidden_estimate(_key, _frame):
        raise AssertionError("estimator must not run below complete-case and exposure floors")

    monkeypatch.setattr(m, "estimate", forbidden_estimate)
    result = m.outcome(key, [("AAA", 2009)], "prereg", "lock", "synthetic-time")
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
    assert result["sample"]["estimator_attempted"] is False
    assert result["gate_checks"]["min_valid_rows"] is False


@pytest.mark.parametrize("failure", ["missing", "uncommitted"])
def test_missing_or_uncommitted_source_lock_blocks_analysis(monkeypatch, failure):
    if failure == "missing":
        monkeypatch.setattr(m, "first_addition", lambda _relative: (
            (_ for _ in ()).throw(RuntimeError("missing first-addition commit"))))
    else:
        monkeypatch.setattr(m, "first_addition", lambda _relative: "synthetic-lock-commit")
        monkeypatch.setattr(m, "committed_unchanged", lambda _relative, _rev: (
            (_ for _ in ()).throw(RuntimeError("uncommitted frozen file"))))

    def forbidden_analysis(_key, _roster):
        raise AssertionError("outcome analysis opened before source lock")

    monkeypatch.setattr(m, "analysis_frame", forbidden_analysis)
    with pytest.raises(RuntimeError, match=("missing first-addition" if failure == "missing"
                                            else "uncommitted frozen file")):
        m.run_or_verify(False)


def test_source_lock_requires_prereg_ancestor(monkeypatch, tmp_path):
    preflight = {"tax": {"synthetic": True}, "epl": {"synthetic": True}}
    lock_path = tmp_path / m.LOCK
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps(m.lock_payload("prereg-rev", preflight)))
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


def test_exact_replay_rejects_artifact_drift(monkeypatch, tmp_path):
    roster = {"tax": [("AAA", 2009)], "epl": [("BBB", 2020)]}
    roster_bytes = b"synthetic-frozen-roster\n"
    roster_path = tmp_path / m.ROSTER
    roster_path.parent.mkdir(parents=True)
    roster_path.write_bytes(roster_bytes)
    monkeypatch.setattr(m, "ROOT", tmp_path)
    monkeypatch.setattr(m, "source_lock_commit", lambda: (
        "lock-rev", {"preregistration_commit": "prereg-rev"}))
    monkeypatch.setattr(m, "source_keys", lambda: roster)
    monkeypatch.setattr(m, "roster_bytes", lambda _rows: roster_bytes)
    monkeypatch.setattr(m, "outcome", lambda key, _roster, _rev, _lock_rev, stamp: (
        {"hypothesis_id": key, "run_utc": stamp}))
    monkeypatch.setattr(m, "artifact_bytes", lambda key, result: {
        "diagnostics.json": (json.dumps(result, sort_keys=True) + "\n").encode(),
        "synthetic.txt": f"{key}: frozen\n".encode()})
    monkeypatch.setattr(m, "summary_bytes", lambda _results: b"synthetic summary\n")
    stamp = "2026-01-01T00:00:00+00:00"
    for key in m.CASE:
        result = {"hypothesis_id": key, "run_utc": stamp}
        dest = tmp_path / m.run_rel(key)
        dest.mkdir(parents=True)
        for name, raw in m.artifact_bytes(key, result).items():
            (dest / name).write_bytes(raw)
    summary = tmp_path / m.SUMMARY
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_bytes(b"synthetic summary\n")
    m.run_or_verify(True)
    (tmp_path / m.run_rel("tax") / "synthetic.txt").write_bytes(b"drift\n")
    with pytest.raises(RuntimeError, match="exact replay mismatch"):
        m.run_or_verify(True)
