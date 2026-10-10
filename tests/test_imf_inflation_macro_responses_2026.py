"""Synthetic and custody gates for the blind IMF inflation response family."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_imf_inflation_macro_responses_2026",
    ROOT / "scripts/run_imf_inflation_macro_responses_2026.py",
)
assert SPEC and SPEC.loader
FAMILY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FAMILY)


def test_prelock_selected_outcome_reader_projects_keys_only(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.append(tuple(columns))
        return pd.DataFrame({
            "country_iso3": ["AAA"] + [""] * 17555,
            "indicator_id": ["NE.CON.PRVT.PC.KD"] * 17556,
            "year": [2000] * 17556,
        })

    monkeypatch.setattr(FAMILY.pd, "read_parquet", fake_read)
    assert FAMILY.read_outcome_keys(Path("/does/not/matter"), "consumption") == {("AAA", 2000)}
    assert seen == [("country_iso3", "indicator_id", "year")]
    assert "value" not in seen[0] and "obs_status" not in seen[0]
    with pytest.raises(RuntimeError, match="selected outcome"):
        FAMILY.read_outcome_keys(Path("/does/not/matter"), "gdp_pc")


def test_bounded_exposure_is_finite_and_symmetric():
    x = FAMILY.exposure(11.0, 0.0)
    assert 0.99 < x < 1.01
    assert FAMILY.exposure(0.0, 11.0) == pytest.approx(-x)
    assert abs(FAMILY.exposure(100000.0, 0.0)) <= 2.0
    assert math.isfinite(FAMILY.exposure(-100000.0, 100000.0))


def test_roster_uses_values_only_for_treatment_and_control(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    values = {
        "inflation": {("AAA", 1995): 10, ("AAA", 1998): 20,
                       ("BBB", 1995): 10, ("BBB", 1998): 20},
        "gdp_pc": {("AAA", 1995): 1000, ("AAA", 1998): 1200,
                   ("BBB", 1995): 1000, ("BBB", 1998): 1200},
    }
    keys = {role: {("AAA", y) for y in (1995, 1998, 2001)}
            | {("BBB", y) for y in (1995, 1998, 2001)} for role in FAMILY.CASES}
    assert FAMILY.candidate_roster(values, keys, {"AAA", "BBB"}) == [
        ("AAA", 1998), ("BBB", 1998),
    ]
    keys["investment"].remove(("BBB", 2001))
    assert FAMILY.candidate_roster(values, keys, {"AAA", "BBB"}) == [("AAA", 1998)]


def test_selected_bounds_status_and_prior_change_are_frozen(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    roster = [("AAA", 2000), ("BBB", 2000), ("CCC", 2000)]
    values = {
        "inflation": {(c, 1997): 0.0 for c in ("AAA", "BBB", "CCC")}
                     | {(c, 2000): 11.0 for c in ("AAA", "BBB", "CCC")},
        "gdp_pc": {(c, 1997): 1000.0 for c in ("AAA", "BBB", "CCC")}
                  | {(c, 2000): 1100.0 for c in ("AAA", "BBB", "CCC")},
    }
    outcome = {
        ("AAA", 1997): (20.0, ""), ("AAA", 2000): (22.0, ""),
        ("AAA", 2003): (24.0, ""),
        ("BBB", 1997): (20.0, ""), ("BBB", 2000): (-1.0, ""),
        ("BBB", 2003): (25.0, ""),
        ("CCC", 1997): (20.0, ""), ("CCC", 2000): (22.0, "E"),
        ("CCC", 2003): (25.0, ""),
    }
    panel, gate = FAMILY.build_panel(roster, values, outcome, "investment")
    assert gate["dropped_invalid_selected_triples"] == 1
    assert gate["dropped_nonblank_selected_status_triples"] == 1
    assert gate["valid_rows"] == 1
    assert panel.iloc[0].outcome_change == 2.0
    assert panel.iloc[0].prior_outcome_change == 2.0
    assert panel.iloc[0].exposure == pytest.approx(FAMILY.exposure(11, 0))
    assert FAMILY.outcome_level("consumption", 0) is None
    assert FAMILY.outcome_level("unemployment", 101) is None
    assert FAMILY.outcome_level("investment", 110) == 110  # no outcome-based upper trimming


def synthetic_panel(beta: float, *, concentrated: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(83941)
    rows = []
    for j in range(32):
        country = f"C{j:02d}"
        for year in range(1995, 2007):
            x = rng.normal(0, 0.85)
            if concentrated:
                x = rng.normal(0, 2.0) if j == 0 else rng.normal(0, .001)
            baseline = rng.normal(20, 3)
            prior = rng.normal(0, 2)
            income = rng.normal(9, .5)
            growth = rng.normal(.04, .02)
            prior_inflation = rng.normal(.2, .5)
            outcome = (beta * x + .06 * baseline + .02 * prior + .03 * income
                       + .1 * growth + .04 * prior_inflation + .01 * j
                       + .02 * (year - 1995) + rng.normal(0, .02))
            rows.append({"country_iso3": country, "year": year,
                         "exposure": x, "prior_inflation": prior_inflation,
                         "baseline_outcome": baseline, "prior_outcome_change": prior,
                         "log_gdp_pc": income, "prior_log_gdp_pc_change": growth,
                         "outcome_change": outcome})
    return pd.DataFrame(rows)


def gate_for(panel: pd.DataFrame):
    up = panel.loc[panel.exposure.ge(FAMILY.MATERIAL_X), "country_iso3"]
    down = panel.loc[panel.exposure.le(-FAMILY.MATERIAL_X), "country_iso3"]
    return {"valid_rows": len(panel), "valid_economies": panel.country_iso3.nunique(),
            "valid_treatment_years": panel.year.nunique(),
            "material_acceleration_rows": len(up),
            "material_acceleration_economies": up.nunique(),
            "material_deceleration_rows": len(down),
            "material_deceleration_economies": down.nunique()}


def lower_synthetic_floors(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_COMPLETE_ROWS", 100)
    monkeypatch.setattr(FAMILY, "MIN_COMPLETE_COUNTRIES", 20)
    monkeypatch.setattr(FAMILY, "MIN_COMPLETE_YEARS", 8)
    monkeypatch.setattr(FAMILY, "MIN_MATERIAL_ROWS", 30)
    monkeypatch.setattr(FAMILY, "MIN_MATERIAL_COUNTRIES", 10)


@pytest.mark.parametrize("role,beta,verdict", [
    ("consumption", -.10, "SUPPORTED"), ("consumption", .10, "REFUTED"),
    ("investment", -1.0, "SUPPORTED"), ("investment", 1.0, "REFUTED"),
    ("unemployment", 1.0, "SUPPORTED"), ("unemployment", -1.0, "REFUTED"),
])
def test_directional_gate_and_bonferroni_on_synthetic_panel(monkeypatch, role, beta, verdict):
    lower_synthetic_floors(monkeypatch)
    panel = synthetic_panel(beta)
    result = FAMILY.estimate(panel, gate_for(panel), role)
    assert result["verdict"] == verdict
    assert result["primary"]["p_value_two_sided"] <= FAMILY.P_MAX
    assert result["primary"]["df_inference"] == panel.country_iso3.nunique() - 1


def test_underpowered_or_concentrated_panels_are_inconclusive(monkeypatch):
    lower_synthetic_floors(monkeypatch)
    panel = synthetic_panel(-1.0)
    gate = gate_for(panel)
    gate["valid_rows"] = 99
    assert FAMILY.estimate(panel, gate, "investment")["verdict"] == "INCONCLUSIVE"
    concentrated = synthetic_panel(-1.0, concentrated=True)
    gate = gate_for(concentrated)
    monkeypatch.setattr(FAMILY, "MIN_MATERIAL_ROWS", 0)
    monkeypatch.setattr(FAMILY, "MIN_MATERIAL_COUNTRIES", 0)
    result = FAMILY.estimate(concentrated, gate, "investment")
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["gate"]["residual_exposure_concentration"]["top_economy"] > .15


def test_chronology_failure_precedes_selected_value_access(monkeypatch):
    opened = []
    def no_lock(_source_root):
        raise RuntimeError("separate source lock missing")
    monkeypatch.setattr(FAMILY, "authorized_measurement_context", no_lock)
    monkeypatch.setattr(FAMILY, "read_outcome_values", lambda *args: opened.append(args))
    with pytest.raises(RuntimeError, match="source lock missing"):
        FAMILY.execute_measured("run", Path("/does/not/matter"))
    assert opened == []


def test_three_specs_match_runner_family():
    for role, case in FAMILY.CASES.items():
        spec = yaml.safe_load((ROOT / FAMILY.spec_path(case)).read_text())
        t = spec["falsification"]["threshold"]
        assert spec["hypothesis_id"] == case["id"]
        assert spec["covers_claims"] == []
        assert t["family_size"] == 3 and t["family_alpha"] == .01
        assert t["p_max_two_sided_bonferroni"] == FAMILY.P_MAX
        assert t["meaningful_abs_beta"] == case["meaningful_beta"]
        assert t["roster_sha256"] == FAMILY.ROSTER_SHA
        assert t["causal_credit"] == 0 and not t["school_score_eligible"]
        assert not t["policy_score_eligible"] and not t["featured_eligible"]
