"""Plano Real stages must not be multiplied by overlapping movement narratives."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compute_country_drift", ROOT / "scripts" / "compute_country_drift.py"
)
assert SPEC and SPEC.loader
DRIFT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIFT)

BRAZIL_PLAN_MOVEMENTS = {
    "brazil_itamar_pmdb_1992_1995",
    "brazil_real_plan_cardoso_1994_2002",
    "brazil_real_plan_1994",
    "brazil_cardoso_ii_2nd_term_1999_2002",
}


def test_plano_real_narratives_preserve_distinct_decision_years() -> None:
    movements = DRIFT.load_movements()
    brazil = [m for m in movements if m["movement_id"] in BRAZIL_PLAN_MOVEMENTS]
    assert {m["movement_id"] for m in brazil} == BRAZIL_PLAN_MOVEMENTS

    umbrella = next(m for m in brazil if m["movement_id"] == "brazil_real_plan_1994")
    assert umbrella["axes_summary"] == []
    assert umbrella["policies"]

    result = DRIFT.build_drift(brazil)
    country = result["countries"]["BRA"]
    assert country["movement_count"] == 4
    assert country["axis_first_year"] == {
        "regulatory.product_market_competition": 1993,
        "monetary.central_bank_independence": 1999,
        "fiscal.transfer_expansion": 2001,
    }
    assert {
        year: country["statist_drift"][result["years"].index(year)]
        for year in (1992, 1993, 1994, 1997, 1999, 2001)
    } == {
        1992: 0.0,
        1993: -2.0,
        1994: -2.0,
        1997: -5.0,
        1999: -7.0,
        2001: -6.0,
    }

    full = DRIFT.build_drift(movements)
    assert (full["year_min"], full["year_max"]) == (1789, 2026)
