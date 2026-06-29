"""Tests for the Berlin Mietspiegel qualified-rent-index panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data" / "derived" / "berlin_mietspiegel_panel.parquet"

GRAIN = [
    "edition_year",
    "location_quality_de",
    "building_age_class_de",
    "dwelling_size_class_de",
]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL_PATH.exists():
        pytest.skip(f"panel not built: {PANEL_PATH}")
    return pd.read_parquet(PANEL_PATH)


def test_panel_exists_and_nonempty(panel: pd.DataFrame) -> None:
    assert PANEL_PATH.exists()
    assert len(panel) > 0


def test_expected_columns_present(panel: pd.DataFrame) -> None:
    expected = {
        "edition_year",
        "country_name",
        "city_name",
        "ieset_city_id",
        "ghsl_city_id",
        "ghsl_city_name",
        "ghsl_match_flag",
        "zeile",
        "location_quality_de",
        "location_quality_norm",
        "building_age_class_de",
        "dwelling_size_class_de",
        "net_cold_rent_lower_eur_m2",
        "net_cold_rent_mean_eur_m2",
        "net_cold_rent_upper_eur_m2",
        "rent_index_type",
        "source_dataset",
        "source_url",
    }
    assert expected.issubset(set(panel.columns))


def test_grain_uniqueness(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(GRAIN).any()
    # Zeile is the official cell index within an edition; it must be unique too.
    assert not panel.duplicated(["edition_year", "zeile"]).any()


def test_rents_positive_and_plausible(panel: pd.DataFrame) -> None:
    for col in (
        "net_cold_rent_lower_eur_m2",
        "net_cold_rent_mean_eur_m2",
        "net_cold_rent_upper_eur_m2",
    ):
        assert panel[col].notna().all(), f"{col} has nulls"
        assert (panel[col] > 0).all(), f"{col} has non-positive values"
        # Net cold rent EUR/m2/month for Berlin sits comfortably in (3, 40).
        assert (panel[col] > 3).all() and (panel[col] < 40).all(), f"{col} out of plausible range"


def test_spanne_ordering(panel: pd.DataFrame) -> None:
    # untere Spanne <= Mittelwert <= obere Spanne for every cell.
    assert (panel["net_cold_rent_lower_eur_m2"] <= panel["net_cold_rent_mean_eur_m2"]).all()
    assert (panel["net_cold_rent_mean_eur_m2"] <= panel["net_cold_rent_upper_eur_m2"]).all()


def test_ghsl_match_flag_present_and_berlin_matched(panel: pd.DataFrame) -> None:
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].all()
    assert (panel["ieset_city_id"] == "ghsl_ucdb_r2024a:5483").all()
    assert (panel["ghsl_city_name"] == "Berlin").all()


def test_original_german_labels_preserved(panel: pd.DataFrame) -> None:
    # The three Wohnlagen must appear with their original German labels.
    wohnlagen = set(panel["location_quality_de"].unique())
    assert {"Einfache Wohnlage", "Mittlere Wohnlage", "Gute Wohnlage"}.issubset(wohnlagen)
    # Building-age classes retain German wording (Bezugsfertigkeit) and m2 units.
    assert panel["building_age_class_de"].str.contains("1918").any()
    assert panel["dwelling_size_class_de"].str.contains("m²").any()


def test_qualified_index_labeling(panel: pd.DataFrame) -> None:
    assert (panel["rent_index_type"] == "qualified_rent_index_legal_reference").all()
    assert panel["source_dataset"].str.contains("Mietspiegel", case=False).all()


def test_single_edition_year_is_recent(panel: pd.DataFrame) -> None:
    years = set(panel["edition_year"].unique())
    assert years, "no edition year"
    assert all(2017 <= int(y) <= 2030 for y in years)
