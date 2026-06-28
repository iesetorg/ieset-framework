from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_city_policy_test_readiness_matrix as readiness_builder  # noqa: E402


def test_city_policy_test_readiness_matrix_marks_ready_and_partial_cities(tmp_path: Path):
    spine = tmp_path / "spine.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "city_rank_2025": 22,
                "city_name": "New York City",
                "country_name": "United States",
                "country_iso3": "USA",
                "population_2025": 19000000,
                "area_km2_2025": 1000,
                "density_per_km2_2025": 19000,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "city_rank_2025": 96,
                "city_name": "San Francisco",
                "country_name": "United States",
                "country_iso3": "USA",
                "population_2025": 4700000,
                "area_km2_2025": 1600,
                "density_per_km2_2025": 2900,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5816",
                "city_rank_2025": 35,
                "city_name": "London",
                "country_name": "United Kingdom",
                "country_iso3": "GBR",
                "population_2025": 12000000,
                "area_km2_2025": 1800,
                "density_per_km2_2025": 6500,
            },
        ]
    ).to_parquet(spine, index=False)

    zillow = tmp_path / "zillow.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "zillow_region_id": 1,
                "month_end": "2025-01-31",
                "zori_usd": 3000,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "zillow_region_id": 2,
                "month_end": "2025-01-31",
                "zori_usd": 3200,
            },
        ]
    ).to_parquet(zillow, index=False)

    permits = tmp_path / "permits.parquet"
    pd.DataFrame(
        [
            {"ieset_city_id": "ghsl_ucdb_r2024a:1461", "year": 2025, "total_units": 100},
        ]
    ).to_parquet(permits, index=False)

    nyc_quality = tmp_path / "nyc_quality.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2025,
                "source_dataset_key": "dob_permit_issuance",
                "value": 10,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2025,
                "source_dataset_key": "hpd_violation",
                "value": 20,
            },
        ]
    ).to_parquet(nyc_quality, index=False)

    sf_quality = tmp_path / "sf_quality.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "year": 2025,
                "source_dataset_key": "building_permit",
                "value": 30,
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:1461",
                "year": 2025,
                "source_dataset_key": "rent_board_inventory",
                "value": 40,
            },
        ]
    ).to_parquet(sf_quality, index=False)

    nyc_reg = tmp_path / "nyc_reg.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:8099",
                "year": 2026,
                "benefit_family": "421a",
                "value_count": 5,
                "unit_count": 100,
                "restricted_unit_count": 20,
            }
        ]
    ).to_parquet(nyc_reg, index=False)

    inputs = {
        "city_spine": spine,
        "zillow_rent": zillow,
        "census_permits": permits,
        "nyc_quality": nyc_quality,
        "datasf_quality": sf_quality,
        "nyc_regulation_proxy": nyc_reg,
        "acs_incidence": tmp_path / "missing_acs.parquet",
    }
    matrix, stats = readiness_builder.build_matrix(inputs)

    nyc = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:8099")].iloc[0]
    assert nyc["rent_control_readiness_tier"] == "case_ready_local_panel"
    assert nyc["rent_control_core_layer_count"] == 4
    assert nyc["supply_response_layer"]
    assert nyc["regulated_stock_or_rent_board_layer"]

    sf = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:1461")].iloc[0]
    assert sf["rent_control_readiness_tier"] == "case_ready_local_panel"
    assert sf["census_permit_total_units"] == 100

    london = matrix[matrix["ieset_city_id"].eq("ghsl_ucdb_r2024a:5816")].iloc[0]
    assert london["rent_control_readiness_tier"] == "spine_only"
    assert stats["tier_counts"]["case_ready_local_panel"] == 2
    assert stats["missing_optional_inputs"] == ["acs_incidence"]

    output = tmp_path / "readiness.parquet"
    artifacts = readiness_builder.write_outputs(
        matrix,
        stats,
        output,
        tmp_path / "manifests",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    assert output.exists()
    assert output.with_suffix(".csv").exists()
    assert output.with_suffix(".json").exists()
    manifest = yaml.safe_load(Path(artifacts["manifest_path"]).read_text())
    assert manifest["entries"][0]["series_id"] == "city_policy_test_readiness_matrix"
