"""Country-year movement vintages must exclude narrower and broader scopes."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_movement_vintages", ROOT / "scripts" / "build_movement_vintages.py"
)
assert SPEC and SPEC.loader
VINTAGES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VINTAGES)


def test_only_national_movements_contribute_to_country_year_vintages(
    tmp_path: Path, monkeypatch
) -> None:
    cases = [
        ("federal", None, ["USA"], "classical_liberal", "fiscal.spending_level"),
        ("california", "subnational", ["USA"], "social_democratic", "regulatory.environmental_stringency"),
        ("eu_wide", "supranational", ["DEU", "FRA"], "ordoliberal", "regulatory.trade_openness"),
    ]
    for movement_id, scope, countries, position_id, axis in cases:
        doc = {
            "movement_id": movement_id,
            "countries": countries,
            "timeframe": {"start": 2006, "end": 2006},
            "position_alignments": [{"position_id": position_id, "alignment": "aligned"}],
            "axes_summary": [{"axis": axis, "direction": "+", "magnitude": "strong"}],
        }
        if scope is not None:
            doc["scope"] = scope
        (tmp_path / f"{movement_id}.yaml").write_text(yaml.safe_dump(doc))
    monkeypatch.setattr(VINTAGES, "MOVEMENTS", tmp_path)

    movements = VINTAGES.load_movements(
        {"classical_liberal", "social_democratic", "ordoliberal"}
    )
    assert [m["movement_id"] for m in movements] == ["federal"]

    axes = VINTAGES.active_axis_rows(movements, end_year=2006)
    positions = VINTAGES.active_position_rows(movements, end_year=2006)
    assert axes[["country_iso3", "series", "value"]].to_records(index=False).tolist() == [
        ("USA", "axis_fiscal_spending_level", 1.0)
    ]
    assert positions[["country_iso3", "position_id", "value"]].to_records(index=False).tolist() == [
        ("USA", "classical_liberal", 1.0)
    ]

    base = pd.DataFrame(
        [(country, 2006) for country in ("USA", "DEU", "FRA")],
        columns=["country_iso3", "year"],
    )
    national_axis = VINTAGES.dense_series(base, axes[["country_iso3", "year", "value"]])
    assert dict(zip(national_axis.country_iso3, national_axis.value)) == {
        "USA": 1.0, "DEU": 0.0, "FRA": 0.0
    }


def test_existing_california_and_eu_records_stay_out_of_national_vintages() -> None:
    movements = VINTAGES.load_movements(set(VINTAGES.load_position_ids()))
    included = {m["movement_id"] for m in movements}
    excluded = {
        "california_climate_regulatory_regime_2006_present",
        "eu_single_market_1993",
        "eu_csrd_sustainability_reporting_2023",
        "eu_green_deal_2020",
        "eu_gdpr_regulatory_stack_2018",
        "eu_reach_chemicals_2007",
    }
    assert included.isdisjoint(excluded)


def test_default_grid_includes_first_national_1789_movement(monkeypatch) -> None:
    monkeypatch.setattr(VINTAGES, "load_vintage_country_years", lambda: (set(), None, None))
    monkeypatch.setattr(VINTAGES, "load_hypothesis_countries", lambda: set())
    movements = [
        {"movement_id": "france_1789", "countries": ["FRA"], "timeframe": {"start": 1789}},
        {"movement_id": "california_1770", "countries": ["USA"], "scope": "subnational", "timeframe": {"start": 1770}},
    ]
    base = VINTAGES.build_base_grid(
        movements, start_year=VINTAGES.DEFAULT_START_YEAR, end_year=1800
    )
    assert (base.year.min(), base.year.max()) == (1789, 1800)
    assert set(base.country_iso3) == {"FRA"}
