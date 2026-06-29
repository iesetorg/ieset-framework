"""Tests for the Portugal INE municipal new-lease median rent panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "derived" / "portugal_ine_municipal_rents_panel.parquet"

EXPECTED_COLUMNS = {
    "municipality_code",
    "municipality_name",
    "country_name",
    "country_iso3",
    "period",
    "period_label",
    "year",
    "quarter",
    "median_rent_eur_per_m2",
    "measure",
    "ieset_city_id",
    "ghsl_city_id",
    "ghsl_city_name",
    "ghsl_city_rank_2025",
    "ghsl_match_flag",
    "ghsl_match_type",
}


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL.exists():
        pytest.skip(f"panel artifact not built: {PANEL}")
    return pd.read_parquet(PANEL)


def test_file_exists() -> None:
    assert PANEL.exists(), f"expected built panel at {PANEL}"


def test_columns_present(panel: pd.DataFrame) -> None:
    assert EXPECTED_COLUMNS.issubset(set(panel.columns)), (
        f"missing columns: {EXPECTED_COLUMNS - set(panel.columns)}"
    )


def test_grain_uniqueness(panel: pd.DataFrame) -> None:
    dupes = panel.duplicated(subset=["municipality_code", "period"]).sum()
    assert dupes == 0, f"{dupes} duplicate (municipality_code, period) rows"


def test_positive_plausible_rents(panel: pd.DataFrame) -> None:
    rents = panel["median_rent_eur_per_m2"]
    assert rents.notna().all(), "null rents present"
    assert (rents > 0).all(), "non-positive rents present"
    # New-lease median rents in Portuguese municipalities are a few EUR/m2 up to
    # roughly mid-teens; bound generously to catch unit/parse errors.
    assert (rents < 40).all(), "implausibly high EUR/m2 rents present"
    assert rents.max() >= 5, "rents implausibly low; likely a parse error"


def test_ghsl_match_flag_present(panel: pd.DataFrame) -> None:
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].dtype == bool or set(
        panel["ghsl_match_flag"].dropna().unique()
    ).issubset({True, False})


def test_lisbon_matched_to_ghsl(panel: pd.DataFrame) -> None:
    lis = panel[panel["municipality_name"] == "Lisboa"]
    assert not lis.empty, "Lisboa rows missing from panel"
    assert lis["ghsl_match_flag"].all(), "Lisboa not matched to GHSL"
    assert lis["ghsl_city_id"].notna().all(), "Lisboa missing ghsl_city_id"


def test_porto_matched_to_ghsl(panel: pd.DataFrame) -> None:
    por = panel[panel["municipality_name"] == "Porto"]
    assert not por.empty, "Porto rows missing from panel"
    assert por["ghsl_match_flag"].all(), "Porto not matched to GHSL"


def test_unmatched_municipalities_retained(panel: pd.DataFrame) -> None:
    # The panel must retain municipalities that do not crosswalk to GHSL,
    # flagged false (only Lisbon and Porto are expected to match).
    assert (~panel["ghsl_match_flag"]).any(), "no unmatched municipalities retained"


def test_original_codes_preserved(panel: pd.DataFrame) -> None:
    # INE municipio codes are alphanumeric (e.g. '1701106' Lisboa, '11A1312' Porto).
    codes = panel["municipality_code"].astype(str)
    assert (codes.str.len() >= 6).all(), "municipality codes look truncated"
    assert "1701106" in set(codes), "expected Lisboa code 1701106 missing"
    assert "11A1312" in set(codes), "expected Porto code 11A1312 missing"


def test_measure_label(panel: pd.DataFrame) -> None:
    assert (
        panel["measure"] == "observed_new_lease_median_rent_eur_per_m2"
    ).all(), "measure label not set to observed new-lease median rent"
