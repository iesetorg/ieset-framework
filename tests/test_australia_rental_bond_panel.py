from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl
import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_australia_rental_bond_panel as builder  # noqa: E402


def write_lodgement_workbook(path: Path, sheet_name: str, rows: list[tuple]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(["NSW Fair Trading Residential Rental Bond Lodgements", None, None, None, None])
    ws.append([None, None, None, None, None])
    ws.append(["Lodgement Date", "Postcode", "Dwelling Type", "Bedrooms", "Weekly Rent"])
    for row in rows:
        ws.append(list(row))
    wb.save(path)
    wb.close()


@pytest.fixture()
def spine(tmp_path: Path) -> Path:
    path = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2324",
                "city_rank_2025": 104,
                "city_name": "Sydney",
                "country_name": "Australia",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1747",
                "city_rank_2025": 114,
                "city_name": "Melbourne",
                "country_name": "Australia",
            },
        ]
    ).to_parquet(path, index=False)
    return path


def test_build_australia_rental_bond_panel_from_lodgement_workbook(tmp_path: Path, spine: Path):
    wb_path = tmp_path / "rentalbond_lodgements_may_2026.xlsx"
    write_lodgement_workbook(
        wb_path,
        "May26 Rental Bond Lodgments",
        [
            # Greater Sydney (postcode 2000) flats, 2 bedrooms
            (datetime(2026, 5, 1), 2000, "F", "2", "700"),
            (datetime(2026, 5, 3), 2000, "F", "2", "740"),
            (datetime(2026, 5, 5), 2000, "F", "2", "780"),
            # Greater Sydney house, unknown rent (counts but not in median)
            (datetime(2026, 5, 6), 2010, "H", "3", "U"),
            # Rest of NSW (postcode 2480 Lismore) house
            (datetime(2026, 5, 2), 2480, "H", "3", "520"),
            (datetime(2026, 5, 4), 2480, "H", "3", "560"),
            # Spurious dwelling code and unknown bedrooms still counted
            (datetime(2026, 5, 7), 2000, "1", "U", "650"),
        ],
    )

    panel, stats = builder.build_panel(city_spine_path=spine, input_files=[wb_path])

    # File written and panel non-empty
    assert len(panel) > 0
    assert stats["panel_rows"] == len(panel)
    assert stats["micro_lodgement_rows"] == 7

    # Grain uniqueness
    grain = ["jurisdiction_code", "period", "geography_id", "dwelling_type_code", "bedroom_group"]
    assert not panel.duplicated(subset=grain).any()

    # ghsl_match_flag present and at least one major metro matched
    assert "ghsl_match_flag" in panel.columns
    syd = panel[panel["geography_id"].eq("greater_sydney")]
    assert syd["ghsl_match_flag"].all()
    assert (syd["ieset_city_id"] == "ghsl_ucdb_r2024a:2324").all()
    assert stats["unique_ieset_city_ids"] >= 1

    # Rents positive and plausible where present
    rents = panel["median_weekly_rent_aud"].dropna()
    assert (rents > 0).all()
    assert (rents < 50000).all()

    # Greater Sydney flat/2br median = median(700,740,780) = 740
    syd_flat_2br = panel[
        panel["geography_id"].eq("greater_sydney")
        & panel["dwelling_type_code"].eq("F")
        & panel["bedroom_group"].eq("2")
    ]
    assert len(syd_flat_2br) == 1
    assert syd_flat_2br["median_weekly_rent_aud"].iloc[0] == 740.0
    assert syd_flat_2br["bond_lodgement_count"].iloc[0] == 3

    # nsw_state aggregate exists and covers all rows for a group present in both geos
    assert "nsw_state" in set(panel["geography_id"])

    # Unknown rent counts as a lodgement but yields null median
    syd_house = panel[
        panel["geography_id"].eq("greater_sydney")
        & panel["dwelling_type_code"].eq("H")
        & panel["bedroom_group"].eq("3")
    ]
    assert len(syd_house) == 1
    assert syd_house["bond_lodgement_count"].iloc[0] == 1
    assert syd_house["rent_observation_count"].iloc[0] == 0
    assert pd.isna(syd_house["median_weekly_rent_aud"].iloc[0])

    # Rent measure labelled as observed bond-lodgement rents
    assert (panel["rent_measure"] == "observed_bond_lodgement_weekly_rent").all()

    # Emit + manifest round-trip
    output = tmp_path / "australia_rental_bond_panel.parquet"
    result = builder.emit(panel, stats, output, datetime(2026, 6, 29, 10, tzinfo=timezone.utc))
    assert output.exists()
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T100000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "australia_rental_bond_panel"
    assert payload["entries"][0]["currency"] == "AUD"
    assert len(result.sha256) == 64
