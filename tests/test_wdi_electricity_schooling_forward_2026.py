"""Focused safeguards for the fixed electricity/schooling family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "schooling", ROOT / "scripts/run_wdi_electricity_schooling_forward_2026.py"
)
assert SPEC and SPEC.loader
schooling = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(schooling)


def _values():
    countries = ["AAA"]
    years = range(schooling.START - schooling.LAG, schooling.END + schooling.HORIZON + 1)
    return {role: {(c, y): 20.0 + y - 1995 for c in countries for y in years}
            for role in schooling.SOURCES}


def test_exact_outcome_endpoints_and_prior_exposure() -> None:
    values = _values()
    for year in range(1995, 2022):
        values["income"][("AAA", year)] = 1000.0 + year
    panel, diag = schooling.panel_for("primary_completion", values, ["AAA"])
    assert diag["complete_pairs"] == 19
    assert len(panel) == 19
    assert panel.iloc[0].electricity_gain_10pp == 0.5
    assert panel.iloc[0].change == 3.0
    values["primary_completion"][("AAA", 2003)] = None
    panel, diag = schooling.panel_for("primary_completion", values, ["AAA"])
    assert diag["complete_pairs"] == 17  # 2003 baseline and 2000 future must both fail
    assert not set(panel.year).intersection({2000, 2003})


def test_small_panel_cannot_emit_public_coefficient() -> None:
    values = _values()
    for year in range(1995, 2022):
        values["income"][("AAA", year)] = 1000.0 + year
    panel, diag = schooling.panel_for("primary_completion", values, ["AAA"])
    estimate, verdict = schooling.calculate(panel, diag)
    assert verdict == "INCONCLUSIVE"
    assert estimate == {}
    assert "min_complete_pairs" in diag["failed_gates"]
    assert "min_countries" in diag["failed_gates"]


def test_fixed_family_denominator_and_zero_score_credit() -> None:
    assert schooling.FAMILY_SIZE == len(schooling.CASES) == 5
    for key in schooling.CASES:
        t = schooling.threshold(key)
        assert t["p_max_two_sided_bonferroni"] == 0.002
        assert t["school_score_eligible"] is False
        assert t["school_score_credit"] == 0
        assert t["policy_score_eligible"] is False
        assert t["policy_score_credit"] == 0
