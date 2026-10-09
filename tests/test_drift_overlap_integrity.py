"""Broad histories must not repeat a narrower reform's national drift step."""
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


def selected(*ids: str) -> list[dict]:
    wanted = set(ids)
    movements = [m for m in DRIFT.load_movements() if m["movement_id"] in wanted]
    assert {m["movement_id"] for m in movements} == wanted
    return movements


def value(result: dict, country: str, axis: str, year: int) -> float:
    return result["countries"][country]["axes"][axis][result["years"].index(year)]


def test_callaghan_imf_adjustment_is_counted_once() -> None:
    result = DRIFT.build_drift(selected(
        "uk_callaghan_imf_1976", "uk_callaghan_labour_1976_1979"
    ))
    gbr = result["countries"]["GBR"]
    assert gbr["movement_count"] == 2
    assert value(result, "GBR", "fiscal.spending_level", 1976) == -2.0
    assert value(result, "GBR", "monetary.monetary_expansion_direction", 1976) == -2.0
    assert value(result, "GBR", "regulatory.labour_market_flexibility", 1976) == -2.0


def test_ira_and_chips_begin_in_2022_without_repeating_2021_infrastructure() -> None:
    result = DRIFT.build_drift(selected(
        "us_biden_administration_broad_2021_2025", "biden_ira_chips_2022"
    ))
    usa = result["countries"]["USA"]
    assert usa["movement_count"] == 2
    assert value(result, "USA", "fiscal.spending_level", 2021) == 3.0
    assert value(result, "USA", "fiscal.spending_level", 2022) == 5.0
    assert value(result, "USA", "fiscal.sectoral_subsidy", 2021) == 0.0
    assert value(result, "USA", "fiscal.sectoral_subsidy", 2022) == 3.0
    assert value(result, "USA", "fiscal.tax_corporate", 2021) == 0.0
    assert value(result, "USA", "fiscal.tax_corporate", 2022) == 1.0
    assert "us_infrastructure_act_2021" not in next(
        m for m in selected("biden_ira_chips_2022")
    )["policies"]


def test_colombia_umbrella_is_context_and_uribe_steps_use_decision_years() -> None:
    movements = selected(
        "colombia_uribe_security_market_reforms_2002_2010",
        "colombia_uribe_santos_duque_market_continuity_2002_2022",
    )
    umbrella = next(m for m in movements if "market_continuity" in m["movement_id"])
    assert umbrella["axes_summary"] == []
    assert umbrella["policies"]

    result = DRIFT.build_drift(movements)
    col = result["countries"]["COL"]
    assert col["movement_count"] == 2
    assert "monetary.central_bank_independence" not in col["axis_first_year"]
    assert col["axis_first_year"]["regulatory.sectoral_licensing"] == 2005
    assert col["axis_first_year"]["regulatory.trade_openness"] == 2009
    assert value(result, "COL", "regulatory.trade_openness", 2002) == 0.0
    assert value(result, "COL", "regulatory.trade_openness", 2009) == 2.0
