from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_acs_place_housing_incidence_panel as acs_builder  # noqa: E402


def test_acs_place_housing_incidence_panel_derives_metrics_and_matches_spine(tmp_path: Path):
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "city_rank_2025": 96,
                "city_name": "San Francisco",
                "country_name": "United States",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:7181",
                "city_rank_2025": 435,
                "city_name": "Minneapolis [Saint Paul]",
                "country_name": "United States",
            },
        ]
    ).to_csv(spine_csv, index=False)

    def row(name: str, state: str, place: str, values: dict[str, object]):
        return [name, *[str(values.get(variable, 0)) for variable in acs_builder.ACS_VARIABLES], state, place]

    header = ["NAME", *acs_builder.ACS_VARIABLES, "state", "place"]

    def fake_fetch(year: int, state_code: str, variables: list[str], api_key: str):
        assert variables == acs_builder.ACS_VARIABLES
        assert api_key == "test-key"
        if state_code == "06":
            values = {
                "B25003_001E": 400,
                "B25003_002E": 160,
                "B25003_003E": 240,
                "B25070_001E": 240,
                "B25070_007E": 20,
                "B25070_008E": 20,
                "B25070_009E": 30,
                "B25070_010E": 50,
                "B25070_011E": 40,
                "B25064_001E": 2500,
                "B25058_001E": 2300,
                "B19013_001E": 120000,
                "B25034_001E": 500,
                "B25034_002E": 20,
                "B25034_003E": 40,
                "B25034_004E": 50,
                "B25034_011E": 150,
                "B25002_001E": 550,
                "B25002_002E": 500,
                "B25002_003E": 50,
                "B07013_001E": 380,
                "B07013_003E": 200,
                "B07013_006E": 160,
                "B07013_009E": 20,
                "B07013_012E": 10,
                "B07013_015E": 5,
                "B07013_018E": 5,
                "B25024_001E": 600,
                "B25024_006E": 40,
                "B25024_007E": 30,
                "B25024_008E": 20,
                "B25024_009E": 10,
            }
            return [header, row("San Francisco city, California", "06", "67000", values)]
        if state_code == "27":
            values = {
                "B25003_001E": 100,
                "B25003_002E": 60,
                "B25003_003E": 40,
                "B25070_001E": 40,
                "B25070_010E": 10,
                "B25002_001E": 120,
                "B25002_003E": 20,
                "B07013_003E": 40,
                "B07013_006E": 30,
                "B07013_009E": 5,
                "B07013_012E": 3,
                "B07013_015E": 2,
                "B25024_001E": 150,
                "B25024_006E": 10,
            }
            return [header, row("St. Paul city, Minnesota", "27", "58000", values)]
        raise AssertionError(state_code)

    panel, stats = acs_builder.build_panel(
        city_spine_path=spine_csv,
        years=[2024],
        states=["06", "27"],
        api_key="test-key",
        fetcher=fake_fetch,
    )

    assert len(panel) == 2
    assert stats["query_count"] == 2
    assert stats["matched_places"] == 2
    sf = panel[panel["acs_place_geoid"].eq("0667000")].iloc[0]
    assert sf["ieset_city_id"] == "ghsl_ucdb_r2024a:1461"
    assert sf["renter_share_occupied_housing_units"] == pytest.approx(0.6)
    assert sf["gross_rent_burden_30plus_renter_households"] == 120
    assert sf["gross_rent_burden_30plus_share"] == pytest.approx(0.6)
    assert sf["gross_rent_burden_50plus_share"] == pytest.approx(0.25)
    assert sf["vacancy_rate"] == pytest.approx(50 / 550)
    assert sf["housing_units_built_2010plus"] == 60
    assert sf["multifamily_5plus_share_structures"] == pytest.approx(100 / 600)
    assert sf["renter_moved_1y_share"] == pytest.approx(40 / 200)
    saint_paul = panel[panel["acs_place_geoid"].eq("2758000")].iloc[0]
    assert saint_paul["ieset_city_id"] == "ghsl_ucdb_r2024a:7181"
    assert saint_paul["manual_review_required"]

    result = acs_builder.emit(
        panel,
        stats,
        tmp_path / "us_acs_place_housing_incidence_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = acs_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_acs_place_housing_incidence_panel"


def test_acs_builder_auto_mode_uses_bulk_without_api_key(tmp_path: Path):
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "city_rank_2025": 96,
                "city_name": "San Francisco",
                "country_name": "United States",
            }
        ]
    ).to_csv(spine_csv, index=False)

    def fake_bulk_fetcher(year: int, variables: list[str]) -> pd.DataFrame:
        assert year == 2024
        assert variables == acs_builder.ACS_VARIABLES
        values = {variable: "0" for variable in variables}
        values.update(
            {
                "B25003_001E": "400",
                "B25003_003E": "240",
                "B25070_001E": "240",
                "B25070_010E": "60",
                "B25002_001E": "500",
                "B25002_003E": "50",
            }
        )
        return pd.DataFrame(
            [
                {
                    "NAME": "San Francisco city, California",
                    **values,
                    "state": "06",
                    "place": "67000",
                    "acs_year": year,
                }
            ]
        )

    panel, stats = acs_builder.build_panel(
        city_spine_path=spine_csv,
        years=[2024],
        states=["06"],
        api_key="",
        source_mode="auto",
        bulk_fetcher=fake_bulk_fetcher,
    )

    assert len(panel) == 1
    assert stats["source_mode"] == "bulk_table_based_summary_file"
    assert not stats["api_key_used"]
    assert stats["bulk_table_files"] == len({acs_builder.bulk_column_for_variable(v)[0] for v in acs_builder.ACS_VARIABLES})
    row = panel.iloc[0]
    assert row["ieset_city_id"] == "ghsl_ucdb_r2024a:1461"
    assert row["renter_share_occupied_housing_units"] == pytest.approx(0.6)
    assert row["source_url"] == acs_builder.BULK_DATA_URL.format(year=2024)


def test_acs_matching_uses_state_guard_for_common_city_names(tmp_path: Path):
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:7833",
                "city_rank_2025": 759,
                "city_name": "Cleveland",
                "country_name": "United States",
            }
        ]
    ).to_csv(spine_csv, index=False)

    raw = pd.DataFrame(
        [
            {"NAME": "Cleveland town, Alabama", "state": "01", "place": "15472"},
            {"NAME": "Cleveland city, Ohio", "state": "39", "place": "16000"},
        ]
    )

    matched = acs_builder.attach_matches(raw, spine_csv).sort_values("state")
    alabama = matched[matched["state"].eq("01")].iloc[0]
    ohio = matched[matched["state"].eq("39")].iloc[0]
    assert pd.isna(alabama["ieset_city_id"])
    assert alabama["match_type"] == "unmatched_or_ambiguous_name"
    assert ohio["ieset_city_id"] == "ghsl_ucdb_r2024a:7833"


def test_acs_builder_requires_api_key(tmp_path: Path):
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "city_rank_2025": 96,
                "city_name": "San Francisco",
                "country_name": "United States",
            }
        ]
    ).to_csv(spine_csv, index=False)

    with pytest.raises(ValueError, match="API key required"):
        acs_builder.build_panel(city_spine_path=spine_csv, years=[2024], states=["06"], api_key="", source_mode="api")
