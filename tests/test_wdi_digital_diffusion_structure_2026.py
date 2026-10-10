"""Synthetic and chronology checks for the blind internet-uptake family."""
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
    "run_wdi_digital_diffusion_structure_2026",
    ROOT / "scripts/run_wdi_digital_diffusion_structure_2026.py",
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
            "indicator_id": ["IC.BUS.NREG"] * 17556,
            "year": [2010] * 17556,
        })

    monkeypatch.setattr(FAMILY.pd, "read_parquet", fake_read)
    assert FAMILY.read_outcome_keys(Path("/does/not/matter"), "entry") == {("AAA", 2010)}
    assert seen == [("country_iso3", "indicator_id", "year")]
    assert "value" not in seen[0] and "obs_status" not in seen[0]
    with pytest.raises(RuntimeError, match="selected outcome"):
        FAMILY.read_outcome_keys(Path("/does/not/matter"), "gdp_pc")


def test_exposure_scale_and_candidate_keys(monkeypatch):
    assert FAMILY.exposure(30.0, 20.0) == pytest.approx(1.0)
    assert FAMILY.exposure(20.0, 30.0) == pytest.approx(-1.0)
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    monkeypatch.setattr(FAMILY, "T_START", 2009)
    monkeypatch.setattr(FAMILY, "T_END", 2009)
    values = {
        "internet": {(c, 2006): 20.0 for c in ("AAA", "BBB")}
                    | {(c, 2009): 30.0 for c in ("AAA", "BBB")},
        "gdp_pc": {(c, 2006): 1000.0 for c in ("AAA", "BBB")}
                  | {(c, 2009): 1200.0 for c in ("AAA", "BBB")},
        "population": {(c, y): 1_000_000.0 for c in ("AAA", "BBB")
                       for y in (2006, 2009, 2012)},
    }
    keys = {role: {(c, y) for c in ("AAA", "BBB") for y in (2006, 2009, 2012)}
            for role in FAMILY.CASES}
    assert FAMILY.candidate_roster(values, keys, {"AAA", "BBB"}) == [
        ("AAA", 2009), ("BBB", 2009)]
    keys["hightech"].remove(("BBB", 2012))
    assert FAMILY.candidate_roster(values, keys, {"AAA", "BBB"}) == [("AAA", 2009)]


def test_selected_bounds_status_population_and_prior_change(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    roster = [("AAA", 2009), ("BBB", 2009), ("CCC", 2009)]
    values = {
        "internet": {(c, 2006): 20.0 for c in ("AAA", "BBB", "CCC")}
                    | {(c, 2009): 30.0 for c in ("AAA", "BBB", "CCC")},
        "gdp_pc": {(c, 2006): 1000.0 for c in ("AAA", "BBB", "CCC")}
                  | {(c, 2009): 1100.0 for c in ("AAA", "BBB", "CCC")},
        "population": {(c, y): 1_000_000.0 for c in ("AAA", "BBB", "CCC")
                       for y in (2006, 2009, 2012)},
    }
    outcome = {
        ("AAA", 2006): (100.0, ""), ("AAA", 2009): (120.0, ""),
        ("AAA", 2012): (140.0, ""),
        ("BBB", 2006): (100.0, ""), ("BBB", 2009): (-1.0, ""),
        ("BBB", 2012): (140.0, ""),
        ("CCC", 2006): (100.0, ""), ("CCC", 2009): (120.0, "E"),
        ("CCC", 2012): (140.0, ""),
    }
    panel, gate = FAMILY.build_panel(roster, values, outcome, "entry")
    assert gate["dropped_invalid_selected_triples"] == 1
    assert gate["dropped_nonblank_selected_status_triples"] == 1
    assert gate["valid_rows"] == 1
    assert panel.iloc[0].outcome_change == pytest.approx(math.log1p(140)-math.log1p(120))
    assert panel.iloc[0].prior_outcome_change == pytest.approx(math.log1p(120)-math.log1p(100))
    assert panel.iloc[0].exposure == 1.0
    assert FAMILY.outcome_level("entry", -1, 1_000_000) is None
    assert FAMILY.outcome_level("services", 101, 1_000_000) is None
    assert FAMILY.outcome_level("hightech", 100, 1_000_000) == 100


def synthetic_panel(beta: float, *, concentrated: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(62491)
    rows = []
    for j in range(60):
        country = f"C{j:02d}"
        for year in range(2009, 2017):
            x = rng.normal(.45, .9)
            if concentrated:
                x = rng.normal(.45, 3.0) if j == 0 else rng.normal(.45, .001)
            baseline = rng.normal(10, 2)
            prior = rng.normal(0, 1)
            income = rng.normal(9, .5)
            growth = rng.normal(.04, .02)
            prior_internet = rng.normal(4, .8)
            outcome = (beta*x + .06*baseline + .02*prior + .03*income
                       + .1*growth + .04*prior_internet + .01*j
                       + .02*(year-2009) + rng.normal(0, .03))
            rows.append({"country_iso3":country,"year":year,"exposure":x,
                         "prior_internet":prior_internet,"baseline_outcome":baseline,
                         "prior_outcome_change":prior,"log_gdp_pc":income,
                         "prior_log_gdp_pc_change":growth,"outcome_change":outcome})
    return pd.DataFrame(rows)


def gate_for(panel: pd.DataFrame):
    rise = panel.loc[panel.exposure.ge(FAMILY.MATERIAL_UP/10), "country_iso3"]
    low = panel.loc[panel.exposure.le(FAMILY.MATERIAL_LOW/10), "country_iso3"]
    return {"valid_rows":len(panel),"valid_economies":panel.country_iso3.nunique(),
            "valid_treatment_years":panel.year.nunique(),
            "material_rise_rows":len(rise),"material_rise_economies":rise.nunique(),
            "low_change_rows":len(low),"low_change_economies":low.nunique()}


@pytest.mark.parametrize("role,beta,verdict", [
    ("entry", .25, "SUPPORTED"), ("entry", -.25, "REFUTED"),
    ("services", 1.0, "SUPPORTED"), ("services", -1.0, "REFUTED"),
    ("hightech", 2.0, "SUPPORTED"), ("hightech", -2.0, "REFUTED"),
])
def test_directional_bonferroni_on_synthetic_panel(role, beta, verdict):
    panel = synthetic_panel(beta)
    result = FAMILY.estimate(panel, gate_for(panel), role)
    assert result["verdict"] == verdict
    assert result["primary"]["p_value_two_sided"] <= FAMILY.P_MAX
    assert result["primary"]["df_inference"] == 59


def test_sparse_gate_precedes_model_construction(monkeypatch):
    panel = synthetic_panel(.25).iloc[:1]
    gate = gate_for(panel)
    monkeypatch.setattr(FAMILY.smf, "ols", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("model opened")))
    assert FAMILY.estimate(panel, gate, "entry")["verdict"] == "INCONCLUSIVE"


def test_influence_gate_rejects_concentrated_synthetic_panel():
    panel = synthetic_panel(.25, concentrated=True)
    gate = gate_for(panel)
    gate.update(material_rise_rows=100, material_rise_economies=30,
                low_change_rows=100, low_change_economies=30)
    result = FAMILY.estimate(panel, gate, "entry")
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


def test_gate_cleared_partial_is_public_descriptive_and_inconclusive_is_archived():
    panel = synthetic_panel(0.0)
    result = FAMILY.estimate(panel, gate_for(panel), "entry")
    assert result["verdict"] == "PARTIAL"
    assert result["primary"] is not None
    assert FAMILY.publication_tier(result["verdict"]) == "public_descriptive_calibration"
    card = FAMILY.result_card("entry", result, "registration", "lock")
    assert "public_descriptive_calibration" in card
    packet = FAMILY.artifact_payload("entry", result, "registration", "lock", "2026-10-10T00:00:00Z")
    assert packet["packet"]["verdict"]["publication_tier"] == "public_descriptive_calibration"
    assert packet["diagnostics"]["publication_tier"] == "public_descriptive_calibration"
    assert packet["manifest"]["publication_tier"] == "public_descriptive_calibration"
    assert packet["chart"]["publication_tier"] == "public_descriptive_calibration"
    assert FAMILY.publication_tier("SUPPORTED") == "public_descriptive_calibration"
    assert FAMILY.publication_tier("REFUTED") == "public_descriptive_calibration"
    assert FAMILY.publication_tier("INCONCLUSIVE") == "inconclusive_archive"
    sparse = FAMILY.estimate(panel.iloc[:1], gate_for(panel.iloc[:1]), "entry")
    assert sparse["verdict"] == "INCONCLUSIVE"
    assert "inconclusive_archive" in FAMILY.result_card("entry", sparse, "registration", "lock")
