from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_stockholm_bostadsformedlingen_queue_panel as stockholm_builder  # noqa: E402


def test_stockholm_queue_panel_normalizes_chart_payloads_and_matches_city(tmp_path: Path):
    spine = tmp_path / "city_universe_top1000.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1693",
                "city_rank_2025": 334,
                "city_name": "Stockholm",
                "country_name": "Sweden",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:75",
                "city_rank_2025": 930,
                "city_name": "Gothenburg",
                "country_name": "Sweden",
            },
        ]
    ).to_parquet(spine, index=False)

    payloads = [
        {
            "year": 2025,
            "queue": "Bostadskön",
            "measure": "rent_band_count",
            "payload": {
                "labels": [
                    {"short": "8-10", "long": "8000 till 10000 kr", "group": 8},
                    {"short": "20 <", "long": "20000 kr eller högre", "group": 20},
                ],
                "datasets": [{"data": [12, 3]}],
            },
        },
        {
            "year": 2025,
            "queue": "Bostadskön",
            "measure": "queue_time_band_count",
            "payload": {
                "labels": [
                    {"short": "0-2", "long": "0 till 2 år", "group": 0},
                    {"short": "20 <", "long": "20 år eller mer", "group": 20},
                ],
                "datasets": [{"data": [5, 7]}],
            },
        },
    ]

    panel, stats = stockholm_builder.build_panel(city_spine_path=spine, payloads=payloads)

    assert len(panel) == 4
    assert stats["unique_ieset_city_ids"] == 1
    assert stats["rent_band_rows"] == 2
    assert stats["queue_time_band_rows"] == 2
    assert stats["rent_band_allocated_dwellings"] == 15
    assert stats["queue_time_allocated_dwellings"] == 12

    rent = panel[panel["measure"].eq("rent_band_count") & panel["band_group"].eq(8)].iloc[0]
    assert rent["ieset_city_id"] == "ghsl_ucdb_r2024a:1693"
    assert rent["ghsl_city_rank_2025"] == 334
    assert rent["band_lower"] == 8000
    assert rent["band_upper"] == 10000
    assert not rent["band_open_upper"]
    assert rent["band_unit"] == "SEK_monthly_rent"

    open_queue = panel[panel["measure"].eq("queue_time_band_count") & panel["band_group"].eq(20)].iloc[0]
    assert open_queue["band_lower"] == 20
    assert pd.isna(open_queue["band_upper"])
    assert open_queue["band_open_upper"]
    assert open_queue["band_unit"] == "queue_years"

    result = stockholm_builder.emit(
        panel,
        stats,
        tmp_path / "stockholm_bostadsformedlingen_queue_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = stockholm_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "stockholm_bostadsformedlingen_queue_panel"
