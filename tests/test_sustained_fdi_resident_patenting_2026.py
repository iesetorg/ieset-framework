"""Blind-source and synthetic estimator checks for the frozen FDI/patent test."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_sustained_fdi_resident_patenting_2026.py"
SPEC = importlib.util.spec_from_file_location("fdi_patent_runner", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_selected_patent_preflight_projects_keys_only(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.append(tuple(columns))
        return pd.DataFrame({
            "country_iso3": ["AFG"] + [""] * 17555,
            "indicator_id": ["IP.PAT.RESD"] * 17556,
            "year": [2004] * 17556,
        })

    monkeypatch.setattr(runner.pd, "read_parquet", fake_read)
    assert runner.read_patent_keys() == {("AFG", 2004)}
    assert seen == [("country_iso3", "indicator_id", "year")]
    with pytest.raises(RuntimeError, match="forbidden"):
        runner.read_control_values("patents")


def test_roster_uses_exact_three_fdi_years_and_patent_keys(monkeypatch):
    monkeypatch.setattr(runner, "COHORT", ("AAA",))
    monkeypatch.setattr(runner, "T_START", 2004)
    monkeypatch.setattr(runner, "T_END", 2005)
    controls = {
        "fdi": {("AAA", 2002): -1, ("AAA", 2003): 5,
                ("AAA", 2004): 5, ("AAA", 2005): 5},
        "gdp_pc": {("AAA", 2004): 1000, ("AAA", 2005): 1000},
        "gdp_growth": {("AAA", 2004): 2, ("AAA", 2005): 2},
        "population": {("AAA", 2004): 6_000_000,
                       ("AAA", 2005): 6_100_000,
                       ("AAA", 2007): 6_200_000,
                       ("AAA", 2008): 6_300_000},
    }
    keys = {("AAA", 2004), ("AAA", 2005), ("AAA", 2007), ("AAA", 2008)}
    assert runner.event_at(controls, "AAA", 2004) == (3.0, 1)
    assert runner.generated_roster(controls, keys) == [("AAA", 2004), ("AAA", 2005)]
    keys.remove(("AAA", 2008))
    assert runner.generated_roster(controls, keys) == [("AAA", 2004)]
    controls["fdi"][("AAA", 2002)] = math.nan
    assert runner.generated_roster(controls, keys) == []


def test_measured_transform_keeps_true_zero_but_rejects_missing_and_status(monkeypatch):
    monkeypatch.setattr(runner, "MIN_YEARS", 1)
    controls = {
        "fdi": {("AAA", y): 4 for y in (2002, 2003, 2004, 2005, 2006)},
        "gdp_pc": {("AAA", y): 1000 for y in (2004, 2005, 2006)},
        "gdp_growth": {("AAA", y): 2 for y in (2004, 2005, 2006)},
        "population": {("AAA", y): 5_000_000 for y in (2004, 2005, 2006, 2007, 2008, 2009)},
    }
    patent = {("AAA", 2004): (0.0, ""), ("AAA", 2007): (5.0, ""),
              ("AAA", 2005): (3.0, "estimated"), ("AAA", 2008): (8.0, ""),
              ("AAA", 2006): (math.nan, ""), ("AAA", 2009): (6.0, "")}
    panel, gate = runner.build_panel([("AAA", 2004), ("AAA", 2005), ("AAA", 2006)], controls, patent)
    assert len(panel) == gate["complete_rows"] == 1
    assert gate["dropped_nonblank_patent_status_pairs"] == 1
    assert gate["dropped_missing_or_invalid_patent_pairs"] == 1
    assert panel.iloc[0].baseline_log_patent_rate == 0.0
    assert panel.iloc[0].outcome_change == math.log(2.0)
    assert panel.iloc[0].x == 1


def synthetic_panel(beta: float) -> pd.DataFrame:
    rng = np.random.default_rng(20261010)
    rows = []
    country_fe = rng.normal(0, 0.04, 40)
    year_fe = rng.normal(0, 0.02, 12)
    for ci in range(40):
        for yi, year in enumerate(range(2004, 2016)):
            x = int(rng.random() < 0.43)
            baseline = 1.2 + 0.04 * ci + rng.normal(0, 0.25)
            income = 8.5 + rng.normal(0, 0.5)
            growth = 2 + rng.normal(0, 1)
            noise = rng.normal(0, 0.03)
            y = (beta * x + 0.09 * baseline + 0.01 * income + 0.003 * growth
                 + country_fe[ci] + year_fe[yi] + noise)
            rows.append({"country_iso3": f"C{ci:02d}", "year": year, "x": x,
                         "baseline_log_patent_rate": baseline,
                         "log_gdp_pc": income, "gdp_growth": growth,
                         "outcome_change": y})
    return pd.DataFrame(rows)


def gate_for(panel: pd.DataFrame) -> dict:
    exposed = panel.loc[panel.x.eq(1)]
    return {"complete_rows": len(panel),
            "complete_countries": panel.country_iso3.nunique(),
            "min_complete_years_retained_country": panel.country_iso3.value_counts().min(),
            "event_rows": len(exposed),
            "event_countries": exposed.country_iso3.nunique(),
            "within_country_switchers": int(panel.groupby("country_iso3").x.nunique().eq(2).sum())}


@pytest.mark.parametrize("beta, expected", [(0.2, "SUPPORTED"), (-0.2, "REFUTED"),
                                            (0.0, "PARTIAL"), (0.02, "PARTIAL"), (-0.02, "PARTIAL")])
def test_directional_rule_on_synthetic_panel(beta, expected):
    panel = synthetic_panel(beta)
    result = runner.estimate(panel, gate_for(panel))
    assert result["verdict"] == expected, result
    assert result["primary"] is not None
    if expected in ("SUPPORTED", "REFUTED") or abs(beta) == 0.02:
        assert result["primary"]["p_value_two_sided"] <= runner.P_MAX
    assert result["gate"]["top_country_residual_x_share"] < runner.MAX_COUNTRY_SHARE
    assert result["gate"]["top_five_country_residual_x_share"] < runner.MAX_FIVE_COUNTRY_SHARE
    assert result["gate"]["top_one_percent_rows_residual_x_share"] < runner.MAX_TOP_ROW_SHARE


def test_switcher_and_concentration_gates_are_enforced(monkeypatch):
    panel = synthetic_panel(0.2)
    gate = gate_for(panel)
    gate["within_country_switchers"] = 24
    assert runner.estimate(panel, gate)["verdict"] == "INCONCLUSIVE"
    gate = gate_for(panel)
    monkeypatch.setattr(runner, "residual_shares", lambda *_args, **_kwargs: (0.16, 0.2, 0.1))
    result = runner.estimate(panel, gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
    assert result["gate"]["top_country_residual_x_share"] == 0.16


def test_selected_patent_value_reader_refuses_without_committed_lock(monkeypatch):
    opened = []
    monkeypatch.setattr(runner, "check_source_lock",
                        lambda *_args: (_ for _ in ()).throw(RuntimeError("lock absent")))
    monkeypatch.setattr(runner.pd, "read_parquet", lambda *_args, **_kwargs: opened.append(True))
    with pytest.raises(RuntimeError, match="lock absent"):
        runner.patent_values_after_lock("prereg", {}, {})
    assert opened == []


def test_run_chronology_fails_before_patent_reader(monkeypatch):
    opened = []
    monkeypatch.setattr(runner, "check_sources", lambda: {})
    monkeypatch.setattr(runner, "preflight", lambda: ({}, {}))
    monkeypatch.setattr(runner, "registration_commit", lambda: "prereg")
    monkeypatch.setattr(runner, "check_source_lock",
                        lambda *_args: (_ for _ in ()).throw(RuntimeError("lock absent")))
    monkeypatch.setattr(runner, "patent_values_after_lock",
                        lambda *_args: opened.append(True))
    with pytest.raises(RuntimeError, match="lock absent"):
        runner.execute_measured("run")
    assert opened == []


def test_spec_threshold_matches_runner():
    assert runner.threshold()["meaningful_beta_min_abs"] == 0.05
    runner.verify_spec()
