from __future__ import annotations

import csv
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_us_census_bps_city_permits_panel as bps_builder  # noqa: E402


def write_bps_zip(path: Path, rows: list[dict[str, object]]):
    fieldnames = [
        "LOCATION_TYPE",
        "PERIOD",
        "UNIQUE_PLACE_ID",
        "STATE_CODE",
        "STATE_NAME",
        "CENSUS_PLACE_CODE",
        "FIPS_PLACE_CODE",
        "COUNTY_CODE",
        "COUNTY_NAME",
        "PLACE_NAME",
        "LOCATION_NAME",
        "CBSA_CODE",
        "CBSA_NAME",
        "ZIP_CODE",
        "YEAR",
        "SURVEY_DATE",
        "FILE_NAME",
        *bps_builder.NUMERIC_COLUMNS,
    ]
    csv_path = path.with_suffix(".csv")
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    with zipfile.ZipFile(path, "w") as zf:
        zf.write(csv_path, "compiled.csv")


def test_census_bps_builder_filters_annual_places_and_crosswalks(tmp_path: Path):
    bps_zip = tmp_path / "bps.zip"
    base = {column: 0 for column in bps_builder.NUMERIC_COLUMNS}
    rows = [
        {
            **base,
            "LOCATION_TYPE": "Place",
            "PERIOD": "Annual",
            "UNIQUE_PLACE_ID": "06389000",
            "STATE_CODE": "06",
            "PLACE_NAME": "San Francisco",
            "YEAR": 2025,
            "SURVEY_DATE": 2025,
            "TOTAL_UNITS": 1444,
            "UNITS_1_UNIT": 20,
            "UNITS_5_UNITS": 1394,
            "TOTAL_VALUE": 287619446,
        },
        {
            **base,
            "LOCATION_TYPE": "Place",
            "PERIOD": "Annual",
            "UNIQUE_PLACE_ID": "06389000",
            "STATE_CODE": "06",
            "PLACE_NAME": "Different Historical Name",
            "YEAR": 1980,
            "SURVEY_DATE": 1980,
            "TOTAL_UNITS": 5,
        },
        {
            **base,
            "LOCATION_TYPE": "Place",
            "PERIOD": "Annual",
            "UNIQUE_PLACE_ID": "27712600",
            "STATE_CODE": "27",
            "PLACE_NAME": "St. Paul",
            "YEAR": 2025,
            "SURVEY_DATE": 2025,
            "TOTAL_UNITS": 357,
            "UNITS_1_UNIT": 100,
            "UNITS_5_UNITS": 210,
        },
        {
            **base,
            "LOCATION_TYPE": "Place",
            "PERIOD": "Annual",
            "UNIQUE_PLACE_ID": "20533500",
            "STATE_CODE": "20",
            "PLACE_NAME": "St. Paul",
            "YEAR": 2025,
            "SURVEY_DATE": 2025,
            "TOTAL_UNITS": 0,
        },
        {
            **base,
            "LOCATION_TYPE": "Place",
            "PERIOD": "Monthly",
            "UNIQUE_PLACE_ID": "06389000",
            "STATE_CODE": "06",
            "PLACE_NAME": "San Francisco",
            "YEAR": 2025,
            "SURVEY_DATE": 202501,
            "TOTAL_UNITS": 12,
        },
    ]
    write_bps_zip(bps_zip, rows)

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

    panel, stats = bps_builder.build_panel(bps_zip, spine_csv)

    assert len(panel) == 4
    assert stats["place_annual_rows"] == 4
    assert stats["panel_rows"] == stats["place_annual_rows"]
    assert stats["matched_places"] == 2
    assert stats["unique_ieset_city_ids"] == 2
    sf = panel[panel["permit_place_name"].eq("San Francisco")].iloc[0]
    assert sf["total_units"] == 1444
    assert sf["units_5_units"] == 1394
    assert sf["ieset_city_id"] == "ghsl_ucdb_r2024a:1461"
    historical = panel[panel["permit_place_name"].eq("Different Historical Name")].iloc[0]
    assert pd.isna(historical["ieset_city_id"])
    saint_paul = panel[(panel["permit_place_name"].eq("St. Paul")) & (panel["state_code"].eq("27"))].iloc[0]
    assert saint_paul["ieset_city_id"] == "ghsl_ucdb_r2024a:7181"
    assert saint_paul["manual_review_required"]
    kansas = panel[(panel["permit_place_name"].eq("St. Paul")) & (panel["state_code"].eq("20"))].iloc[0]
    assert pd.isna(kansas["ieset_city_id"])

    result = bps_builder.emit(
        panel,
        stats,
        bps_zip,
        tmp_path / "us_city_permits_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = bps_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_city_permits_panel"
