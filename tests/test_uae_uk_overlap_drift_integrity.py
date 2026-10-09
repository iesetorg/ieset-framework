"""Shared UAE and UK decisions should produce one national drift step each."""
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


def _selected_movements(*movement_ids: str) -> list[dict]:
    selected = [
        movement for movement in DRIFT.load_movements()
        if movement["movement_id"] in movement_ids
    ]
    assert {movement["movement_id"] for movement in selected} == set(movement_ids)
    return selected


def _value(drift: dict, country: str, axis: str, year: int) -> float:
    return drift["countries"][country]["axes"][axis][drift["years"].index(year)]


def test_uae_corporate_tax_is_one_2022_law_step() -> None:
    movements = _selected_movements(
        "uae_emirate_state_capitalism_1971_present",
        "uae_mbz_presidency_2022_present",
    )
    tax_entries = [
        (movement["movement_id"], entry)
        for movement in movements
        for entry in movement["axes_summary"]
        if entry["axis"] == "fiscal.tax_corporate"
    ]
    assert len(tax_entries) == 1
    assert tax_entries[0][0] == "uae_mbz_presidency_2022_present"
    assert tax_entries[0][1]["drift_attribution_year"] == 2022

    drift = DRIFT.build_drift(movements)
    assert _value(drift, "ARE", "fiscal.tax_corporate", 1971) == 0.0
    assert _value(drift, "ARE", "fiscal.tax_corporate", 2021) == 0.0
    assert _value(drift, "ARE", "fiscal.tax_corporate", 2022) == 2.0


def test_uk_tca_and_free_movement_are_one_2020_step_per_axis() -> None:
    movements = _selected_movements(
        "uk_may_conservative_2016_2019",
        "uk_brexit_2016_2020",
        "uk_johnson_conservative_2019_2022",
    )
    for axis, step in (
        ("regulatory.trade_openness", -3.0),
        ("regulatory.immigration_openness", -2.0),
    ):
        entries = [
            (movement["movement_id"], entry)
            for movement in movements
            for entry in movement["axes_summary"]
            if entry["axis"] == axis
        ]
        assert len(entries) == 1
        assert entries[0][0] == "uk_brexit_2016_2020"
        assert entries[0][1]["drift_attribution_year"] == 2020

        drift = DRIFT.build_drift(movements)
        assert _value(drift, "GBR", axis, 2016) == 0.0
        assert _value(drift, "GBR", axis, 2019) == 0.0
        assert _value(drift, "GBR", axis, 2020) == step
