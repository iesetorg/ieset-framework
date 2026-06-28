from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_nyc_open_data_housing_quality_panel as nyc_builder  # noqa: E402


def test_nyc_open_data_quality_panel_builds_long_annual_panel(tmp_path: Path):
    spine_csv = tmp_path / "city_universe_top1000.csv"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "city_rank_2025": 22,
                "city_name": "New York City",
                "country_name": "United States",
            }
        ]
    ).to_csv(spine_csv, index=False)

    def fake_fetch(dataset_id: str, query: str):
        if dataset_id == "ipu4-2q9a":
            if "2025" in query:
                return [
                    {
                        "borough": "BROOKLYN",
                        "job_type": "NB",
                        "permit_type": "NB",
                        "residential": "YES",
                        "permit_status": "ISSUED",
                        "filing_status": "INITIAL",
                        "value": "12",
                    }
                ]
            return []
        if dataset_id == "ygpa-z7cr":
            return [
                {
                    "year": "2025",
                    "borough": "BROOKLYN",
                    "major_category": "HEAT/HOT WATER",
                    "type": "HEAT",
                    "complaint_status": "CLOSE",
                    "value": "30",
                }
            ]
        if dataset_id == "wvxf-dwi5":
            return [
                {
                    "year": "2025",
                    "boro": "BROOKLYN",
                    "class": "C",
                    "rentimpairing": "N",
                    "violationstatus": "Open",
                    "value": "7",
                }
            ]
        raise AssertionError(dataset_id)

    def fake_metadata(dataset_id: str):
        return {"id": dataset_id, "name": f"dataset {dataset_id}", "columns": []}

    panel, stats = nyc_builder.build_panel(
        city_spine_path=spine_csv,
        start_year=2025,
        end_year=2026,
        fetcher=fake_fetch,
        metadata_fetcher=fake_metadata,
    )

    assert len(panel) == 3
    assert stats["query_count"] == 4
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:8099"}
    assert set(panel["borough"]) == {"BROOKLYN"}
    assert panel["value"].sum() == 49
    assert stats["datasets"]["dob_permit_issuance"]["value_sum"] == 12
    assert stats["datasets"]["hpd_complaint_problem"]["value_sum"] == 30
    assert stats["datasets"]["hpd_violation"]["value_sum"] == 7

    result = nyc_builder.emit(
        panel,
        stats,
        tmp_path / "us_city_rent_control_quality_leakage_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = nyc_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "us_city_rent_control_quality_leakage_panel"
