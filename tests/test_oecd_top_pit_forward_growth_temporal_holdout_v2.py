"""False-positive guards for the frozen modern top-PIT growth holdout."""
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_oecd_top_pit_forward_growth_temporal_holdout_v2.py"
spec = importlib.util.spec_from_file_location("top_pit_growth_v2", RUNNER)
assert spec and spec.loader
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_imprecise_null_never_becomes_no_harm_support():
    verdict, _ = study.classify_interval(-0.7, 0.2, [-0.1, -0.2, 0.0])
    assert verdict == "PARTIAL"
    verdict, _ = study.classify_interval(-0.31, 0.1, [-0.1, 0.0])
    assert verdict == "PARTIAL"


def test_both_interval_and_country_deletions_must_clear_margin():
    assert study.classify_interval(-0.29, 0.2, [-0.1, 0.1])[0] == "SUPPORTED"
    assert study.classify_interval(-0.29, 0.2, [-0.31, 0.1])[0] == "PARTIAL"
    assert study.classify_interval(-0.8, -0.31, [-0.5, -0.4])[0] == "REFUTED"
    assert study.classify_interval(-0.8, -0.31, [-0.5, -0.2])[0] == "PARTIAL"


def test_frozen_contract_is_one_credit_zero_school():
    threshold = study.threshold()
    assert threshold["family_size"] == 1
    assert threshold["family_alpha"] == 0.005
    assert threshold["meaningful_harm_pp_annual_per_ten_tax_pp"] == -0.3
    assert threshold["min_complete_rows"] == 450
    assert threshold["school_score_eligible"] is False
    assert threshold["policy_score_eligible"] is False
    assert threshold["featured_eligible"] is False
