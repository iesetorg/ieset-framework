from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_datasf_housing_quality_panel as datasf_builder  # noqa: E402


def test_datasf_quality_panel_builds_long_annual_panel(tmp_path: Path):
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

    def fake_fetch(dataset_id: str, query: str):
        if dataset_id == "i98e-djp9":
            return [
                {
                    "year": "2025",
                    "neighborhoods_analysis_boundaries": "Mission",
                    "supervisor_district": "9",
                    "permit_type_definition": "new construction wood frame",
                    "adu": "Y",
                    "value": "12",
                }
            ]
        if dataset_id == "gm2e-bten":
            return [
                {
                    "year": "2025",
                    "analysis_neighborhood": "Mission",
                    "supervisor_district": "9",
                    "receiving_division": "Housing Inspection Services",
                    "status": "Active",
                    "value": "30",
                }
            ]
        if dataset_id == "nbtm-fbw5":
            return [
                {
                    "year": "2025",
                    "neighborhoods_analysis_boundaries": "Mission",
                    "supervisor_district": "9",
                    "nov_category_description": "interior surfaces section",
                    "work_without_permit": "N",
                    "unsafe_building": "Y",
                    "value": "7",
                }
            ]
        if dataset_id == "gdc7-dmcn":
            return [
                {
                    "year": "2025",
                    "analysis_neighborhood": "Mission",
                    "supervisor_district": "9",
                    "case_type_name": "Housing Inventory - Unit information (2025)",
                    "occupancy_type": "Occupied by non-owner",
                    "bedroom_count": "1",
                    "value": "101",
                }
            ]
        if dataset_id == "6swy-cmkq":
            return [
                {
                    "year": "2025",
                    "neighborhoods_analysis_boundaries": "Mission",
                    "supervisor_district": "9",
                    "filing_party": "tenant",
                    "priority": "Decrease in Services",
                    "value": "6",
                }
            ]
        if dataset_id == "5cei-gny5":
            if "ellis_act_withdrawal = true" in query:
                return [
                    {
                        "year": "2025",
                        "neighborhood": "Mission",
                        "supervisor_district": "9",
                        "value": "2",
                    }
                ]
            if " = true" in query:
                return []
            return [
                {
                    "year": "2025",
                    "neighborhood": "Mission",
                    "supervisor_district": "9",
                    "value": "10",
                }
            ]
        if dataset_id == "wmam-7g8d":
            return [
                {
                    "year": "2025",
                    "analysis_neighborhood": "Mission",
                    "supervisor_district": "9",
                    "value": "4",
                }
            ]
        raise AssertionError(dataset_id)

    def fake_metadata(dataset_id: str):
        return {"id": dataset_id, "name": f"dataset {dataset_id}", "columns": []}

    panel, stats = datasf_builder.build_panel(
        city_spine_path=spine_csv,
        start_year=2025,
        end_year=2026,
        fetcher=fake_fetch,
        metadata_fetcher=fake_metadata,
    )

    assert len(panel) == 8
    assert stats["query_count"] == 16
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:1461"}
    assert set(panel["neighborhood"]) == {"Mission"}
    assert panel["value"].sum() == 172
    assert stats["datasets"]["building_permit"]["value_sum"] == 12
    assert stats["datasets"]["dbi_complaint"]["value_sum"] == 30
    assert stats["datasets"]["dbi_notice_of_violation"]["value_sum"] == 7
    assert stats["datasets"]["rent_board_inventory"]["value_sum"] == 101
    assert stats["datasets"]["rent_board_petition"]["value_sum"] == 6
    assert stats["datasets"]["eviction_notice"]["value_sum"] == 12
    assert stats["datasets"]["buyout_agreement"]["value_sum"] == 4
    assert set(panel.loc[panel["source_dataset_key"].eq("eviction_notice"), "category_1"]) == {
        "all_eviction_notices",
        "ellis_act_withdrawal",
    }

    result = datasf_builder.emit(
        panel,
        stats,
        tmp_path / "us_sf_rent_control_quality_leakage_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = datasf_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_sf_rent_control_quality_leakage_panel"
