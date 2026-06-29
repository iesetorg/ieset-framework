from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_uk_mhclg_house_building_panel as mhclg_builder  # noqa: E402


def test_uk_mhclg_house_building_panel_normalizes_supply_and_matches_cities(tmp_path: Path):
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
            "fiscal_year": "2023-24",
            "fiscal_year_start": 2023,
            "fiscal_year_end": 2024,
            "DCLG code": "E08000025",
            "FormerONSCode": "00CN",
            "Current ONS code": "E08000025",
            "Authority data": "Birmingham",
            "Private Enterprise Starts": "100",
            "Housing Association Starts": "20",
            "Local Authority Starts": "10",
            "All Starts": "130",
            "Private Enterprise Completions": "90",
            "Housing Association Completions": "20",
            "Local Authority Completions": "0",
            "All Completions": "110",
        },
        {
            "fiscal_year": "2023-24",
            "fiscal_year_start": 2023,
            "fiscal_year_end": 2024,
            "DCLG code": "K5030",
            "FormerONSCode": "00AA",
            "Current ONS code": "E09000001",
            "Authority data": "City of London",
            "Private Enterprise Starts": "30",
            "Housing Association Starts": "0",
            "Local Authority Starts": "0",
            "All Starts": "30",
            "Private Enterprise Completions": "40",
            "Housing Association Completions": "0",
            "Local Authority Completions": "0",
            "All Completions": "40",
        },
        {
            "fiscal_year": "2023-24",
            "fiscal_year_start": 2023,
            "fiscal_year_end": 2024,
            "DCLG code": "Z0116",
            "FormerONSCode": "00HB",
            "Current ONS code": "E06000023",
            "Authority data": "Bristol, City of",
            "Private Enterprise Starts": "410",
            "Housing Association Starts": "280",
            "Local Authority Starts": "30",
            "All Starts": "720",
            "Private Enterprise Completions": "660",
            "Housing Association Completions": "100",
            "Local Authority Completions": "0",
            "All Completions": "760",
        },
        {
            "fiscal_year": "2023-24",
            "fiscal_year_start": 2023,
            "fiscal_year_end": 2024,
            "DCLG code": "",
            "FormerONSCode": "",
            "Current ONS code": "",
            "Authority data": "England",
            "Private Enterprise Starts": "101120",
            "Housing Association Starts": "32270",
            "Local Authority Starts": "3070",
            "All Starts": "136450",
            "Private Enterprise Completions": "122150",
            "Housing Association Completions": "35320",
            "Local Authority Completions": "2850",
            "All Completions": "160330",
        },
    ]

    panel, stats = mhclg_builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 3
    assert stats["matched_local_authorities"] == 3
    birmingham = panel[panel["local_authority_code"].eq("E08000025")].iloc[0]
    assert birmingham["ieset_city_id"] == "ghsl_ucdb_r2024a:3888"
    assert birmingham["all_starts"] == 130
    assert birmingham["all_completions"] == 110

    london = panel[panel["local_authority_code"].eq("E09000001")].iloc[0]
    assert london["ieset_city_id"] == "ghsl_ucdb_r2024a:5816"
    assert london["match_type"] == "london_borough_to_ghsl"

    bristol = panel[panel["local_authority_code"].eq("E06000023")].iloc[0]
    assert bristol["local_authority_name_norm"] == "BRISTOL"
    assert bristol["ieset_city_id"] == "ghsl_ucdb_r2024a:3058"

    result = mhclg_builder.emit(
        panel,
        stats,
        tmp_path / "uk_mhclg_house_building_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = mhclg_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T020000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "uk_mhclg_house_building_panel"
