from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_hong_kong_rvd_private_domestic_panel as builder  # noqa: E402


def blank_frame(rows: int, cols: int) -> pd.DataFrame:
    return pd.DataFrame([[None for _ in range(cols)] for _ in range(rows)])


def write_rvd_fixture_workbooks(rental_index_path: Path, supply_path: Path) -> None:
    rental_index = blank_frame(14, 28)
    rental_index.iloc[11, 2] = 2024
    rental_index.iloc[11, 5] = 210.8
    rental_index.iloc[11, 26] = 190.5
    rental_index.iloc[12, 2] = 2025
    rental_index.iloc[12, 26] = 196.7
    with pd.ExcelWriter(rental_index_path) as writer:
        rental_index.to_excel(writer, sheet_name="Annual  按年", header=False, index=False)

    completions = blank_frame(17, 16)
    completions.iloc[15, 2] = 2024
    completions.iloc[15, 4] = 100
    completions.iloc[15, 14] = 500
    stock = blank_frame(17, 16)
    stock.iloc[15, 2] = 2024
    stock.iloc[15, 4] = 1000
    stock.iloc[15, 14] = 5000
    vacancy = blank_frame(17, 16)
    vacancy.iloc[15, 2] = 2024
    vacancy.iloc[15, 4] = 10
    vacancy.iloc[15, 5] = 0.01
    vacancy.iloc[15, 14] = 60
    vacancy.iloc[15, 15] = 0.03
    take_up = blank_frame(14, 16)
    take_up.iloc[12, 2] = 2024
    take_up.iloc[12, 4] = 300
    take_up.iloc[12, 8] = 40
    take_up.iloc[12, 12] = 340
    with pd.ExcelWriter(supply_path) as writer:
        completions.to_excel(writer, sheet_name="Completions_落成量", header=False, index=False)
        stock.to_excel(writer, sheet_name="Stock_總存量", header=False, index=False)
        vacancy.to_excel(writer, sheet_name="Vacancy_空置量", header=False, index=False)
        take_up.to_excel(writer, sheet_name="Take-up_入住量", header=False, index=False)


def test_build_hong_kong_rvd_private_domestic_panel(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:11185",
                "city_rank_2025": 93,
                "city_name": "Hong Kong",
                "country_name": "China",
                "country_iso3": None,
                "population_2025": 4807599,
                "area_km2_2025": 280,
                "density_per_km2_2025": 17170,
            }
        ]
    ).to_parquet(spine, index=False)
    rental_index = tmp_path / "his_data_3.xlsx"
    supply = tmp_path / "private_domestic.xlsx"
    write_rvd_fixture_workbooks(rental_index, supply)

    panel, stats = builder.build_panel(city_spine_path=spine, rental_index_path=rental_index, supply_path=supply)

    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:11185"}
    assert stats["start_year"] == 2024
    assert stats["end_year"] == 2025
    assert stats["measure_counts"]["rental_index"] == 3
    assert stats["measure_counts"]["vacancy_rate"] == 2
    all_classes = panel[
        panel["measure"].eq("rental_index")
        & panel["property_class"].eq("ALL")
        & panel["year"].eq(2025)
    ].iloc[0]
    assert all_classes["value"] == 196.7
    vacancy_total_rate = panel[
        panel["measure"].eq("vacancy_rate")
        & panel["property_class"].eq("TOTAL")
    ].iloc[0]
    assert vacancy_total_rate["value"] == 0.03

    output = tmp_path / "hong_kong.parquet"
    fetch_ts = datetime(2026, 6, 29, 9, tzinfo=timezone.utc)
    result = builder.emit(panel, stats, output, fetch_ts)
    manifest = builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T090000Z")

    assert output.exists()
    payload = yaml.safe_load(manifest.read_text())
    assert payload["pipeline"] == "hong_kong_rvd_private_domestic_panel"
    assert payload["entries"][0]["series_id"] == "hong_kong_rvd_private_domestic_panel"
