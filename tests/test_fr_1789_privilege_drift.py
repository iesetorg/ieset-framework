"""The 1789 French privilege score is a narrow legal-content step."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_ID = "fr_august_decrees_1789"
MOVEMENT_ID = "fr_constituent_provincial_privilege_abolition_1789"
CONTEXT_ID = "fr_constituent_assembly_legal_reordering_1789_1791"


def test_privilege_step_has_legal_date_and_only_changes_french_rule_of_law() -> None:
    spec = importlib.util.spec_from_file_location(
        "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
    )
    assert spec and spec.loader
    drift = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drift)

    policy = yaml.safe_load((ROOT / "policies" / f"{POLICY_ID}.yaml").read_text())
    movement = yaml.safe_load((ROOT / "movements" / f"{MOVEMENT_ID}.yaml").read_text())
    assert policy["timeframe"]["effective_date"] == "1789-11-03"
    assert set(policy["enacted_by"]) == {MOVEMENT_ID, CONTEXT_ID}
    assert movement["policies"] == [POLICY_ID]
    context = yaml.safe_load((ROOT / "movements" / f"{CONTEXT_ID}.yaml").read_text())
    assert context["country_drift_role"] == "context_only"
    assert context["country_drift_primary_movement"] == MOVEMENT_ID
    assert [(a["axis"], a["direction"], a["magnitude"]) for a in movement["axes_summary"]] == [
        ("institutional.rule_of_law", "+", "weak")
    ]

    authored = drift.load_movements()
    with_step = drift.build_drift(authored)
    without_step = drift.build_drift(
        [m for m in authored if m["movement_id"] not in {MOVEMENT_ID, CONTEXT_ID}]
    )
    assert with_step["year_min"] == 1789
    assert with_step["countries"]["FRA"]["axis_first_year"]["institutional.rule_of_law"] == 1789
    assert with_step["countries"]["FRA"]["axes"]["institutional.rule_of_law"][0] == 1.0

    for country, target in with_step["countries"].items():
        baseline = without_step["countries"][country]
        for axis, series in target["axes"].items():
            old_by_year = dict(zip(without_step["years"], baseline["axes"][axis]))
            for year, value in zip(with_step["years"], series):
                if year not in old_by_year:
                    continue
                expected_delta = 1.0 if (country, axis) == ("FRA", "institutional.rule_of_law") else 0.0
                assert value - old_by_year[year] == expected_delta
        assert target["statist_drift"][-1] == baseline["statist_drift"][-1]
        assert target["composite_first_year"] == baseline["composite_first_year"]
