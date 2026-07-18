from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "policy_contrast_wave_100.py"
SPEC = importlib.util.spec_from_file_location("policy_contrast_wave_100", MODULE_PATH)
assert SPEC and SPEC.loader
wave = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wave)


def test_wave_has_exactly_100_unique_hypotheses() -> None:
    rows = wave.configs()
    ids = [row["hypothesis_id"] for row in rows]
    assert len(rows) == 100
    assert len(set(ids)) == 100
    assert Counter(row["cohort"] for row in rows) == {
        "us_minimum_wage": 30,
        "us_fiscal_policy": 20,
        "international_policy": 50,
    }


def test_every_hypothesis_is_within_the_requested_twenty_year_window() -> None:
    for row in wave.configs():
        start, end = row["period"]
        assert 2006 <= start <= end <= 2026


def test_specs_encode_exact_decision_and_data_gates() -> None:
    for row in wave.configs():
        spec = wave.build_spec(row)
        assert spec["status"] == "pre_registered"
        assert spec["evidence_type"] == "associational"
        assert spec["claim_direction"] == row["expected_sign"]
        threshold = spec["falsification"]["threshold"]
        assert threshold["expected_sign"] == row["expected_sign"]
        assert threshold["p_max"] == 0.10
        assert threshold["min_observations"] == row["min_observations"]
        assert threshold["min_units"] == row["min_units"]
        assert threshold["min_contrast_gap"] == row["contrast_min"]


def test_preflight_never_estimates_coefficients() -> None:
    rows = wave.preflight_all()
    assert len(rows) == 100
    assert all(row["coefficient_estimated"] is False for row in rows)
    assert all(row["passed"] for row in rows)
