from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_zillow_city_rent_panel as zillow_builder  # noqa: E402


def test_zillow_city_rent_panel_reshapes_and_crosswalks(tmp_path: Path):
    zillow_csv = tmp_path / "zillow.csv"
    pd.DataFrame(
        [
            {
                "RegionID": 1,
                "SizeRank": 0,
                "RegionName": "New York",
                "RegionType": "city",
                "StateName": "NY",
                "State": "NY",
                "Metro": "New York metro",
                "CountyName": "Queens County",
                "2026-04-30": 3900.0,
                "2026-05-31": 4000.0,
            },
            {
                "RegionID": 2,
                "SizeRank": 1,
                "RegionName": "Saint Paul",
                "RegionType": "city",
                "StateName": "MN",
                "State": "MN",
                "Metro": "Twin Cities",
                "CountyName": "Ramsey County",
                "2026-04-30": 1400.0,
                "2026-05-31": None,
            },
            {
                "RegionID": 3,
                "SizeRank": 2,
                "RegionName": "Portland",
                "RegionType": "city",
                "StateName": "OR",
                "State": "OR",
                "Metro": "Portland metro",
                "CountyName": "Multnomah County",
                "2026-04-30": 1800.0,
                "2026-05-31": 1810.0,
            },
            {
                "RegionID": 4,
                "SizeRank": 3,
                "RegionName": "Portland",
                "RegionType": "city",
                "StateName": "ME",
                "State": "ME",
                "Metro": "Portland ME",
                "CountyName": "Cumberland County",
                "2026-04-30": 1600.0,
                "2026-05-31": 1610.0,
            },
        ]
    ).to_csv(zillow_csv, index=False)
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "city_rank_2025": 22,
                "city_name": "New York City",
                "country_name": "United States",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:7181",
                "city_rank_2025": 435,
                "city_name": "Minneapolis [Saint Paul]",
                "country_name": "United States",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:4941",
                "city_rank_2025": 277,
                "city_name": "Portland",
                "country_name": "United States",
            },
        ]
    ).to_csv(spine_csv, index=False)

    panel, stats = zillow_builder.build_panel(zillow_csv, spine_csv)

    assert len(panel) == 7
    assert stats["matched_regions"] == 2
    assert stats["unique_ieset_city_ids"] == 2
    assert set(panel.loc[panel["zillow_region_name"].eq("New York"), "ieset_city_id"]) == {
        "ghsl_ucdb_r2024a:8099"
    }
    saint_paul = panel[panel["zillow_region_name"].eq("Saint Paul")].iloc[0]
    assert saint_paul["ieset_city_id"] == "ghsl_ucdb_r2024a:7181"
    assert saint_paul["manual_review_required"]
    assert panel.loc[panel["zillow_region_name"].eq("Portland"), "ieset_city_id"].isna().all()

    result = zillow_builder.emit(
        panel,
        stats,
        zillow_csv,
        tmp_path / "us_city_rent_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = zillow_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_city_rent_panel"
