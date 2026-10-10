"""Synthetic gates for the prospective remittance/schooling/entry family."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_remittance_schooling_entry_family_2026",
    ROOT / "scripts" / "run_remittance_schooling_entry_family_2026.py",
)
assert SPEC and SPEC.loader
FAMILY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FAMILY)


def test_selected_outcome_preflight_projects_keys_only(monkeypatch):
    seen = []

    def fake_read(_path, *, columns):
        seen.append(tuple(columns))
        return pd.DataFrame({
            "country_iso3": ["AAA"] + [""] * 17555,
            "indicator_id": ["SE.SEC.ENRR"] * 17556,
            "year": [2006] * 17556,
        })

    monkeypatch.setattr(FAMILY.pd, "read_parquet", fake_read)
    keys = FAMILY.read_outcome_keys("enrolment", {"AAA"})
    assert keys == {("AAA", 2006)}
    assert seen == [("country_iso3", "indicator_id", "year")]
    assert "value" not in seen[0] and "obs_status" not in seen[0]
    with pytest.raises(RuntimeError, match="forbidden"):
        FAMILY.read_value_series("enrolment", {"AAA"})


def test_candidate_roster_uses_exact_keys_and_valid_treatment_controls(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    remittance = {
        ("AAA", 2005): 1.0, ("AAA", 2006): 2.0,
        ("BBB", 2005): 0.0, ("BBB", 2006): math.nan,
    }
    gdp_pc = {("AAA", 2006): 1000.0, ("BBB", 2006): 1000.0}
    growth = {("AAA", 2006): 3.0, ("BBB", 2006): 3.0}
    keys = {
        "enrolment": {("AAA", 2006), ("AAA", 2008), ("BBB", 2006), ("BBB", 2008)},
        "registrations": {("AAA", 2006), ("AAA", 2007), ("BBB", 2006), ("BBB", 2007)},
    }
    assert FAMILY.candidate_roster(remittance, gdp_pc, growth, keys, {"AAA", "BBB"}) == [
        ("AAA", 2006)
    ]
    keys["registrations"].remove(("AAA", 2007))
    assert FAMILY.candidate_roster(remittance, gdp_pc, growth, keys, {"AAA", "BBB"}) == []


def test_measured_transform_keeps_over_100_enrolment_and_zero_registrations(monkeypatch):
    monkeypatch.setattr(FAMILY, "MIN_YEARS", 1)
    roster = [("AAA", 2006), ("BBB", 2006)]
    controls = {
        "remittances": {
            ("AAA", 2005): 2.0, ("AAA", 2006): 3.5,
            ("BBB", 2005): 1.0, ("BBB", 2006): 2.0,
        },
        "gdp_pc": {("AAA", 2006): 1000.0, ("BBB", 2006): 2000.0},
        "gdp_growth": {("AAA", 2006): 2.0, ("BBB", 2006): 3.0},
    }
    school = {
        ("AAA", 2006): (120.0, ""), ("AAA", 2008): (123.5, ""),
        ("BBB", 2006): (75.0, ""), ("BBB", 2008): (80.0, "flag"),
    }
    panel, gate = FAMILY.build_measured_panel(
        roster, controls, school, FAMILY.CASES["enrolment"]
    )
    assert gate["valid_rows"] == 1 and gate["dropped_nonblank_outcome_status_pairs"] == 1
    assert panel.iloc[0].baseline_outcome == 120.0
    assert panel.iloc[0].outcome_change == 3.5
    assert panel.iloc[0].remittance_change_pp == 1.5

    entry = {
        ("AAA", 2006): (0.0, ""), ("AAA", 2007): (3.0, ""),
        ("BBB", 2006): (5.0, ""), ("BBB", 2007): (math.nan, ""),
    }
    panel, gate = FAMILY.build_measured_panel(
        roster, controls, entry, FAMILY.CASES["registrations"]
    )
    assert gate["valid_rows"] == 1 and gate["dropped_missing_or_invalid_outcome_pairs"] == 1
    assert panel.iloc[0].baseline_outcome == 0.0
    assert panel.iloc[0].outcome_change == math.log(4)


def synthetic_panel(beta: float, *, concentrated: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(7901)
    rows = []
    for country_index in range(40):
        country = f"C{country_index:02d}"
        for year in range(2006, 2016):
            exposure = (
                (1.25 if country_index % 2 else -1.25)
                + (rng.normal(0, 2.0) if not concentrated
                   else (rng.normal(0, 4.0) if country_index == 0
                         else rng.normal(0, 0.001)))
            )
            baseline = rng.normal(50, 8)
            income = rng.normal(9, 0.4)
            growth = rng.normal(2, 1)
            outcome = (
                beta * exposure + 0.15 * baseline + 0.2 * income
                + 0.1 * growth + 0.12 * country_index + 0.05 * (year - 2006)
                + rng.normal(0, 0.03)
            )
            rows.append({
                "country_iso3": country, "year": year,
                "remittance_change_pp": exposure,
                "baseline_outcome": baseline, "log_gdp_pc": income,
                "gdp_growth": growth, "outcome_change": outcome,
            })
    return pd.DataFrame(rows)


def gate_for(panel: pd.DataFrame) -> dict:
    material = panel.remittance_change_pp.abs().ge(1)
    return {
        "valid_rows": len(panel),
        "valid_countries": panel.country_iso3.nunique(),
        "material_exposure_rows": int(material.sum()),
        "material_exposure_countries": panel.loc[material, "country_iso3"].nunique(),
    }


@pytest.mark.parametrize(
    ("beta", "expected"),
    [(0.4, "SUPPORTED"), (-0.4, "REFUTED"), (0.01, "PARTIAL")],
)
def test_frozen_directional_rule_on_balanced_synthetic_panel(beta, expected):
    panel = synthetic_panel(beta)
    result = FAMILY.estimate(panel, gate_for(panel), FAMILY.CASES["enrolment"])
    assert result["verdict"] == expected
    assert result["primary"] is not None
    assert result["primary"]["top_country_residualized_exposure_share"] < 0.30
    if expected != "PARTIAL":
        assert result["primary"]["p_value_two_sided"] <= 0.005


def test_single_country_residualized_exposure_fails_concentration_gate():
    panel = synthetic_panel(0.4, concentrated=True)
    result = FAMILY.estimate(panel, gate_for(panel), FAMILY.CASES["enrolment"])
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
    assert result["gate"]["top_country_residualized_exposure_share"] > 0.30


def test_chronology_failure_precedes_any_selected_measurement(monkeypatch):
    opened = []

    def uncommitted():
        raise RuntimeError("missing committed registration")

    monkeypatch.setattr(FAMILY, "authorized_measurement_context", uncommitted)
    monkeypatch.setattr(
        FAMILY, "read_outcome_values",
        lambda *args: opened.append(args),
    )
    with pytest.raises(RuntimeError, match="committed registration"):
        FAMILY.execute_measured("run")
    assert opened == []
