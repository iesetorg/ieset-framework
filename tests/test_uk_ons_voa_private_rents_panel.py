from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_uk_ons_voa_private_rents_panel as uk_builder  # noqa: E402


def test_uk_ons_voa_private_rents_panel_normalizes_local_authorities_and_matches_cities(tmp_path: Path):
    spine = tmp_path / "city_universe_top1000.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5816",
                "city_rank_2025": 34,
                "city_name": "London",
                "country_name": "United Kingdom",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3888",
                "city_rank_2025": 197,
                "city_name": "Birmingham",
                "country_name": "United Kingdom",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3058",
                "city_rank_2025": 818,
                "city_name": "Bristol",
                "country_name": "United Kingdom",
            },
        ]
    ).to_parquet(spine, index=False)

    rows = [
        {
            "period_start": "2022-10-01",
            "period_end": "2023-09-30",
            "LA Code1": "4605",
            "Area Code1": "E08000025",
            "Area": "Birmingham",
            "bedroom_category": "all_categories",
            "bedroom_label": "All categories",
            "Count of rents": "1000",
            "Mean": "975",
            "Lower quartile": "700",
            "Median": "850",
            "Upper quartile": "1100",
        },
        {
            "period_start": "2022-10-01",
            "period_end": "2023-09-30",
            "LA Code1": "5030",
            "Area Code1": "E09000001",
            "Area": "City of London",
            "bedroom_category": "all_categories",
            "bedroom_label": "All categories",
            "Count of rents": "50",
            "Mean": "2300",
            "Lower quartile": "1800",
            "Median": "2159",
            "Upper quartile": "2800",
        },
        {
            "period_start": "2022-10-01",
            "period_end": "2023-09-30",
            "LA Code1": "116",
            "Area Code1": "E06000023",
            "Area": "Bristol, City of UA",
            "bedroom_category": "two_bedrooms",
            "bedroom_label": "Two Bedrooms",
            "Count of rents": "420",
            "Mean": "1320",
            "Lower quartile": "1100",
            "Median": "1300",
            "Upper quartile": "1500",
        },
        {
            "period_start": "2022-10-01",
            "period_end": "2023-09-30",
            "LA Code1": "",
            "Area Code1": "E12000007",
            "Area": "London",
            "bedroom_category": "all_categories",
            "bedroom_label": "All categories",
            "Count of rents": "10000",
            "Mean": "1700",
            "Lower quartile": "1200",
            "Median": "1625",
            "Upper quartile": "2200",
        },
    ]

    panel, stats = uk_builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 3
    assert stats["matched_local_authorities"] == 3
    birmingham = panel[panel["local_authority_code"].eq("E08000025")].iloc[0]
    assert birmingham["ieset_city_id"] == "ghsl_ucdb_r2024a:3888"
    assert birmingham["median_monthly_rent_gbp"] == 850

    london = panel[panel["local_authority_code"].eq("E09000001")].iloc[0]
    assert london["ieset_city_id"] == "ghsl_ucdb_r2024a:5816"
    assert london["match_type"] == "london_borough_to_ghsl"

    bristol = panel[panel["local_authority_code"].eq("E06000023")].iloc[0]
    assert bristol["local_authority_name_norm"] == "BRISTOL"
    assert bristol["ieset_city_id"] == "ghsl_ucdb_r2024a:3058"
    assert bristol["bedroom_category"] == "two_bedrooms"

    result = uk_builder.emit(
        panel,
        stats,
        tmp_path / "uk_ons_voa_private_rents_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = uk_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "uk_ons_voa_private_rents_panel"
