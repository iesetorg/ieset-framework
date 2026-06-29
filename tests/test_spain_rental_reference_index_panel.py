"""Tests for the Spain MIVAU SERPAVI rental reference-index panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data" / "derived" / "spain_rental_reference_index_panel.parquet"

GRAIN = ["municipality_code", "period", "dwelling_segment_code"]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL_PATH.exists():
        pytest.skip(f"panel not built: {PANEL_PATH}")
    return pd.read_parquet(PANEL_PATH)


def test_panel_exists_and_nonempty(panel: pd.DataFrame) -> None:
    assert PANEL_PATH.exists()
    assert len(panel) > 1000


def test_grain_uniqueness(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(GRAIN).any()


def test_required_columns_present(panel: pd.DataFrame) -> None:
    required = {
        "year",
        "period",
        "municipality_code",
        "municipality_name",
        "province_code",
        "province_name",
        "dwelling_segment",
        "ref_rent_per_m2_eur_median",
        "ref_rent_per_m2_eur_p25",
        "ref_rent_per_m2_eur_p75",
        "ref_rent_monthly_eur_median",
        "ghsl_match_flag",
        "ieset_city_id",
        "value_type",
        "is_reference_not_observed",
    }
    assert required.issubset(set(panel.columns))


def test_ghsl_match_flag_present_and_boolean(panel: pd.DataFrame) -> None:
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].dropna().isin([True, False]).all()
    assert panel["ghsl_match_flag"].any()


def test_madrid_or_barcelona_matched(panel: pd.DataFrame) -> None:
    matched = panel[panel["ghsl_match_flag"]]
    codes = set(matched["municipality_code"].unique())
    # Madrid 28079, Barcelona 08019
    assert {"28079", "08019"} & codes, f"neither Madrid nor Barcelona matched; got {codes}"
    # Matched rows carry a GHSL identity.
    assert matched["ieset_city_id"].notna().all()
    assert matched["ghsl_city_id"].notna().all()


def test_target_cities_crosswalked(panel: pd.DataFrame) -> None:
    matched_codes = set(panel.loc[panel["ghsl_match_flag"], "municipality_code"].unique())
    # Sevilla (41091) must crosswalk to the English GHSL name "Seville".
    sev = panel[(panel["municipality_code"] == "41091") & panel["ghsl_match_flag"]]
    if not sev.empty:
        assert (sev["ghsl_city_name"] == "Seville").all()
    assert len(matched_codes) >= 2


def test_rents_positive_and_plausible(panel: pd.DataFrame) -> None:
    m2 = panel["ref_rent_per_m2_eur_median"].dropna()
    monthly = panel["ref_rent_monthly_eur_median"].dropna()
    assert (m2 > 0).all()
    assert (monthly > 0).all()
    # Spanish reference EUR/m2/month sits well under 100; whole-dwelling under ~10k.
    assert m2.max() < 100
    assert monthly.max() < 10000


def test_index_range_ordering(panel: pd.DataFrame) -> None:
    sub = panel.dropna(
        subset=["ref_rent_per_m2_eur_p25", "ref_rent_per_m2_eur_median", "ref_rent_per_m2_eur_p75"]
    )
    assert (sub["ref_rent_per_m2_eur_p25"] <= sub["ref_rent_per_m2_eur_median"] + 1e-6).all()
    assert (sub["ref_rent_per_m2_eur_median"] <= sub["ref_rent_per_m2_eur_p75"] + 1e-6).all()


def test_original_codes_preserved(panel: pd.DataFrame) -> None:
    # INE municipality codes are 5-char zero-padded strings.
    codes = panel["municipality_code"].astype(str)
    assert codes.str.fullmatch(r"\d{5}").all()
    assert "28079" in set(codes)
    # Original Spanish municipality names preserved.
    assert (panel["municipality_name"] == "Sevilla").any()


def test_reference_vs_observed_labeling(panel: pd.DataFrame) -> None:
    assert (panel["value_type"] == "official_reference_index").all()
    assert panel["is_reference_not_observed"].all()
    assert "value_basis" in panel.columns


def test_year_coverage(panel: pd.DataFrame) -> None:
    years = set(panel["year"].unique())
    assert 2024 in years
    assert min(years) <= 2015
