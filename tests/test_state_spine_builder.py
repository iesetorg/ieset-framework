from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_state_spine_admin1 as builder  # noqa: E402


TIGER_STATE_ROWS = [
    ("01", "AL", "Alabama"),
    ("02", "AK", "Alaska"),
    ("04", "AZ", "Arizona"),
    ("05", "AR", "Arkansas"),
    ("06", "CA", "California"),
    ("08", "CO", "Colorado"),
    ("09", "CT", "Connecticut"),
    ("10", "DE", "Delaware"),
    ("11", "DC", "District of Columbia"),
    ("12", "FL", "Florida"),
    ("13", "GA", "Georgia"),
    ("15", "HI", "Hawaii"),
    ("16", "ID", "Idaho"),
    ("17", "IL", "Illinois"),
    ("18", "IN", "Indiana"),
    ("19", "IA", "Iowa"),
    ("20", "KS", "Kansas"),
    ("21", "KY", "Kentucky"),
    ("22", "LA", "Louisiana"),
    ("23", "ME", "Maine"),
    ("24", "MD", "Maryland"),
    ("25", "MA", "Massachusetts"),
    ("26", "MI", "Michigan"),
    ("27", "MN", "Minnesota"),
    ("28", "MS", "Mississippi"),
    ("29", "MO", "Missouri"),
    ("30", "MT", "Montana"),
    ("31", "NE", "Nebraska"),
    ("32", "NV", "Nevada"),
    ("33", "NH", "New Hampshire"),
    ("34", "NJ", "New Jersey"),
    ("35", "NM", "New Mexico"),
    ("36", "NY", "New York"),
    ("37", "NC", "North Carolina"),
    ("38", "ND", "North Dakota"),
    ("39", "OH", "Ohio"),
    ("40", "OK", "Oklahoma"),
    ("41", "OR", "Oregon"),
    ("42", "PA", "Pennsylvania"),
    ("44", "RI", "Rhode Island"),
    ("45", "SC", "South Carolina"),
    ("46", "SD", "South Dakota"),
    ("47", "TN", "Tennessee"),
    ("48", "TX", "Texas"),
    ("49", "UT", "Utah"),
    ("50", "VT", "Vermont"),
    ("51", "VA", "Virginia"),
    ("53", "WA", "Washington"),
    ("54", "WV", "West Virginia"),
    ("55", "WI", "Wisconsin"),
    ("56", "WY", "Wyoming"),
    ("60", "AS", "American Samoa"),
    ("66", "GU", "Guam"),
    ("69", "MP", "Commonwealth of the Northern Mariana Islands"),
    ("72", "PR", "Puerto Rico"),
    ("78", "VI", "United States Virgin Islands"),
]


def _write_tiger_fixture(path: Path) -> Path:
    pd.DataFrame(
        [
            {
                "STATEFP": state_fips,
                "GEOID": state_fips,
                "STUSPS": state_abbr,
                "NAME": state_name,
                "LSAD": "00",
            }
            for state_fips, state_abbr, state_name in TIGER_STATE_ROWS
        ]
    ).to_parquet(path, index=False)
    return path


def test_build_from_census_tiger_mints_us_state_spine(tmp_path: Path):
    tiger_path = _write_tiger_fixture(tmp_path / "tiger_state_geographies.parquet")

    universe, crosswalks, stats = builder.build_from_census_tiger(tiger_path)

    assert len(universe) == 56
    assert len(crosswalks) == 168
    assert stats["state_rows"] == 50
    assert stats["federal_district_rows"] == 1
    assert stats["territory_rows"] == 5
    assert "US-CA" in set(universe["ieset_state_id"])
    assert {"US-AS", "US-MP"} <= set(universe["ieset_state_id"])
    assert universe["source_system"].eq("us_census_tiger_state_geographies").all()
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
    assert df["source_system"].eq("us_census_tiger_state_geographies").all()
