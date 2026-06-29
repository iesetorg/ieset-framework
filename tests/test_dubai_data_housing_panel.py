from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_dubai_data_housing_panel as dubai_builder  # noqa: E402


def test_dubai_data_housing_panel_normalizes_rent_and_supply_rows(tmp_path: Path):
    spine = tmp_path / "city_universe_top1000.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1007",
                "city_rank_2025": 100,
                "city_name": "Dubai",
                "country_name": "United Arab Emirates",
            }
        ]
    ).to_parquet(spine, index=False)

    datasets = {
        "residential_rent_price_index": [
            {
                "Year": 2026,
                "Month": "January",
                "Month_Number": 1,
                "Quarter": "First Quarter",
                "Quarter_Number": 1,
                "Type": "Units - New",
                "Weight": "30.34",
                "Value": 115.62,
                "sort_id": 1,
            }
        ],
        "building_permits": [
            {
                "Year": 2026,
                "Month": "January",
                "Quarter": "First Quarter",
                "Type": "Private Villa",
                "Title": "Number",
                dubai_builder.AR_DESCRIPTION_COL: "new build",
                "Value": 220,
                "sort_id": 1,
            },
            {
                "Year": 2026,
                "Month": "January",
                "Quarter": "First Quarter",
                "Type": "Industrial Buildings",
                "Title": "Number",
                "Value": 99,
                "sort_id": 2,
            },
        ],
        "completed_buildings": [
            {
                "Year": 2026,
                "Month": "January",
                "Month_Number": 1,
                "Quarter": "First Quarter",
                "Quarter_Number": 1,
                "Title": "Number of Residential Apartments",
                "Description": "Number",
                "Value": 1234,
                "sort_id": 1,
            }
        ],
    }

    panel, stats = dubai_builder.build_panel(city_spine_path=spine, datasets=datasets)

    assert len(panel) == 4
    assert stats["unique_ieset_city_ids"] == 1
    assert stats["rent_index_rows"] == 1
    assert stats["building_permit_rows"] == 1
    assert stats["completed_building_rows"] == 1
    assert stats["housing_supply_relevant_rows"] == 2

    rent = panel[panel["source_dataset_key"].eq("residential_rent_price_index")].iloc[0]
    assert rent["ieset_city_id"] == "ghsl_ucdb_r2024a:1007"
    assert rent["period"] == "2026-01"
    assert rent["segment_norm"] == "UNITS NEW"
    assert rent["weight"] == 30.34
    assert rent["value"] == 115.62

    permit = panel[panel["building_type"].eq("Private Villa")].iloc[0]
    assert permit["statistic"] == "permit_count"
    assert permit["unit"] == "count"
    assert permit["housing_supply_relevant"]

    industrial = panel[panel["building_type"].eq("Industrial Buildings")].iloc[0]
    assert not industrial["housing_supply_relevant"]

    result = dubai_builder.emit(
        panel,
        stats,
        tmp_path / "dubai_data_housing_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = dubai_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "dubai_data_housing_panel"
