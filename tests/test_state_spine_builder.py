from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_state_spine_admin1 as builder  # noqa: E402


def test_build_from_usdol_mints_us_state_spine():
    try:
        usdol_path = builder.latest_vintage("usdol", "state_minimum_wage_history")
    except FileNotFoundError:
        pytest.skip("USDOL state minimum-wage vintage is not available")

    universe, crosswalks, stats = builder.build_from_usdol(usdol_path)

    assert len(universe) == 54
    assert len(crosswalks) == 162
    assert stats["state_rows"] == 50
    assert stats["federal_district_rows"] == 1
    assert stats["territory_rows"] == 3
    assert "US-CA" in set(universe["ieset_state_id"])
    assert set(crosswalks["source_system"]) == {"iso_3166_2", "us_fips_state", "us_state_abbr"}
    assert crosswalks["manual_review_required"].eq(False).all()


def test_state_spine_outputs_have_expected_columns_when_present():
    parquet_path = REPO_ROOT / "data" / "derived" / "state_universe_admin1.parquet"
    if not parquet_path.exists():
        pytest.skip("state spine output has not been generated")

    import pandas as pd

    df = pd.read_parquet(parquet_path)

    assert {"ieset_state_id", "country_iso3", "state_fips", "iso_3166_2", "admin1_kind"} <= set(df.columns)
    assert df["ieset_state_id"].is_unique
    assert df["country_iso3"].eq("USA").all()
