from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_singapore_hdb_ura_rental_panel as builder  # noqa: E402


def write_spine(path: Path) -> None:
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
    ).to_parquet(path, index=False)


def test_build_singapore_hdb_ura_rental_panel(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    write_spine(spine)
    hdb_rows = [
        {
            "rent_approval_date": "2026-05",
            "town": "ANG MO KIO",
            "block": "105",
            "street_name": "ANG MO KIO AVE 4",
            "flat_type": "4-ROOM",
            "monthly_rent": "3,500",
        },
        {
            "rent_approval_date": "2026-05",
            "town": "SEMBAWANG",
            "block": "120",
            "street_name": "CANBERRA CRES",
            "flat_type": "4-ROOM",
            "monthly_rent": "3200",
        },
        {
            "rent_approval_date": "2026-05",
            "town": "SEMBAWANG",
            "block": "121",
            "street_name": "CANBERRA CRES",
            "flat_type": "5-ROOM",
            "monthly_rent": "-",
        },
    ]
    ura_rows = [
        {
            "qtr": "2026-Q1",
            "project_name": "AMBER PARK",
            "postal_district": "15",
            "25th_percentile": "6.41",
            "median": "7.43",
            "75th_percentile": "8.11",
            "rental_contracts": "28",
        }
    ]

    panel, stats = builder.build_panel(city_spine_path=spine, hdb_rows=hdb_rows, ura_rows=ura_rows)

    assert len(panel) == 3
    assert set(panel["source_dataset_key"]) == {"hdb_approval", "ura_private_non_landed"}
    assert panel.loc[panel["town_norm"].eq("SEMBAWANG"), "ieset_city_id"].iloc[0] == "ghsl_ucdb_r2024a:345"
    assert panel.loc[panel["town_norm"].eq("ANG MO KIO"), "ieset_city_id"].iloc[0] == "ghsl_ucdb_r2024a:178"
    assert panel.loc[panel["source_dataset_key"].eq("hdb_approval"), "monthly_rent_sgd"].sum() == 6700
    ura = panel[panel["source_dataset_key"].eq("ura_private_non_landed")].iloc[0]
    assert ura["rent_median_sgd_psf"] == 7.43
    assert ura["rental_contracts"] == 28
    assert stats["unique_ieset_city_ids"] == 2
    assert stats["hdb_approval_rows"] == 2
    assert stats["ura_private_non_landed_rows"] == 1

    output = tmp_path / "singapore_hdb_ura.parquet"
    fetch_ts = datetime(2026, 6, 29, 7, tzinfo=timezone.utc)
    result = builder.emit(panel, stats, output, fetch_ts)
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T070000Z")

    assert output.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["pipeline"] == "singapore_hdb_ura_rental_panel"
    assert payload["entries"][0]["series_id"] == "singapore_hdb_ura_rental_panel"
