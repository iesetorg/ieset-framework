from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_singapore_hdb_median_rent_panel as builder  # noqa: E402


def test_build_singapore_hdb_median_rent_panel(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:178",
                "city_rank_2025": 85,
                "city_name": "Singapore",
                "country_name": "Singapore",
                "country_iso3": "SGP",
                "population_2025": 5117759,
                "area_km2_2025": 683,
                "density_per_km2_2025": 7493,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:345",
                "city_rank_2025": 547,
                "city_name": "Sembawang",
                "country_name": "Singapore",
                "country_iso3": "SGP",
                "population_2025": 960308,
                "area_km2_2025": 119,
                "density_per_km2_2025": 8070,
            },
        ]
    ).to_parquet(spine, index=False)
    rows = [
        {"quarter": "2005-Q2", "town": "ANG MO KIO", "flat_type": "3-RM", "median_rent": "800"},
        {"quarter": "2005-Q2", "town": "ANG MO KIO", "flat_type": "4-RM", "median_rent": "-"},
        {"quarter": "2026-Q1", "town": "SEMBAWANG", "flat_type": "4-RM", "median_rent": "3,200"},
    ]

    panel, stats = builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 2
    assert set(panel["quarter"]) == {"2005-Q2", "2026-Q1"}
    assert set(panel["median_monthly_rent_sgd"]) == {800.0, 3200.0}
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:178"}
    assert stats["town_count"] == 2
    assert stats["flat_type_count"] == 2

    output = tmp_path / "singapore.parquet"
    fetch_ts = datetime(2026, 6, 29, 5, tzinfo=timezone.utc)
    result = builder.emit(panel, stats, output, fetch_ts)
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T050000Z")

    assert output.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["pipeline"] == "singapore_hdb_median_rent_panel"
    assert payload["entries"][0]["series_id"] == "singapore_hdb_median_rent_panel"
