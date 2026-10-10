"""An EU treaty umbrella must not create identical national drift steps."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)


def test_maastricht_umbrella_and_children_do_not_score_national_movements() -> None:
    movement_id = "maastricht_convergence_criteria_1992"
    movements = DRIFT.load_movements()
    maastricht = next(m for m in movements if m["movement_id"] == movement_id)
    assert maastricht["scope"] == "supranational"
    assert maastricht["timeframe"]["start"] == 1992
    assert set(maastricht["countries"]) == {
        "BEL", "DNK", "DEU", "GRC", "ESP", "FRA", "IRL", "ITA",
        "LUX", "NLD", "PRT", "GBR",
    }

    expected_policy_years = {
        "maastricht_treaty_1992": 1992,
        "stability_growth_pact_1997": 1997,
        "ecb_statute_1998": 1998,
    }
    for policy_id, year in expected_policy_years.items():
        policy = yaml.safe_load((ROOT / "policies" / f"{policy_id}.yaml").read_text())
        assert policy["scope"] == "supranational"
        assert policy["timeframe"]["start"] == year
        assert policy["enacted_by"] == [movement_id]
        if policy_id == "maastricht_treaty_1992":
            assert policy["timeframe"]["signed_date"] == "1992-02-07"
            assert policy["timeframe"]["effective_date"] == "1993-11-01"

    with_treaty = DRIFT.build_drift(movements)
    without_treaty = DRIFT.build_drift(
        [m for m in movements if m["movement_id"] != movement_id]
    )
    assert with_treaty == without_treaty
    assert with_treaty["year_min"] == 1789
