from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_nyc_rent_regulation_tax_benefit_panel as nyc_reg_builder  # noqa: E402


def test_nyc_rent_regulation_tax_benefit_panel_builds_proxy_rows(tmp_path: Path):
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
        if dataset_id == "myn9-hwsy":
            return [
                {"exempt_code": "5114", "sdea_code": "48806", "description": "421A 25 YR NO CAP", "legal_ref": "RPTL 421A"},
                {"exempt_code": "1920", "sdea_code": "48076", "description": "J51", "legal_ref": "DOF1214"},
            ]
        if dataset_id == "muvi-b6kx":
            return [
                {
                    "year": "2026",
                    "boro": "1",
                    "nys_exmp_code": "48806",
                    "exmp_code": "5114",
                    "records": "12",
                    "parcels": "6",
                    "exemption_amount": "1000",
                },
                {
                    "year": "2026",
                    "boro": "2",
                    "nys_exmp_code": "48076",
                    "exmp_code": "1920",
                    "records": "20",
                    "parcels": "10",
                    "exemption_amount": "2000",
                },
            ]
        if dataset_id == "rgyu-ii48":
            return [{"taxyr": "2026", "tccode": "J51", "tcsubcode": "J51", "records": "30", "parcels": "15", "abatement_amount": "300.5"}]
        if dataset_id == "y7az-s7wc":
            return [{"tax_year": "2018", "b": "3", "records": "40", "exemption_amount": "4000", "abatement_amount": "500"}]
        if dataset_id == "pq4c-wbq4":
            return [
                {
                    "year": "2024",
                    "presumed_borough": "BROOKLYN",
                    "reported_affordability_option": "OPTION B",
                    "records": "2",
                    "units": "100",
                    "restricted_units": "25",
                }
            ]
        if dataset_id == "rrtd-iyd7":
            return [
                {
                    "year": "2026",
                    "reported_property_borough": "QUEENS",
                    "reported_affordability_option": "OPTION A",
                    "records": "3",
                    "units": "120",
                    "restricted_units": "30",
                }
            ]
        if dataset_id == "tesw-yqqr":
            return [{"year": "2026", "boro": "MANHATTAN", "records": "50", "registrations": "49", "buildings": "48"}]
        if dataset_id == "64uk-42ks":
            return [{"borough": "MN", "tax_lots": "60", "residential_units": "700", "total_units": "750"}]
        raise AssertionError(dataset_id)

    def fake_metadata(dataset_id: str):
        return {"id": dataset_id, "name": f"dataset {dataset_id}", "columns": []}

    panel, stats = nyc_reg_builder.build_panel(
        city_spine_path=spine_csv,
        start_year=2007,
        end_year=2026,
        fetcher=fake_fetch,
        metadata_fetcher=fake_metadata,
    )

    assert len(panel) == 8
    assert stats["query_count"] == 8
    assert set(panel["ieset_city_id"]) == {"ghsl_ucdb_r2024a:8099"}
    assert {"421a", "j51", "421a16", "485x", "denominator"}.issubset(set(panel["benefit_family"]))
    assert panel["value_count"].sum() == 217
    assert panel["parcel_count"].sum() == 140
    assert panel["unit_count"].sum() == 970
    assert panel["restricted_unit_count"].sum() == 755
    assert panel["exemption_amount"].sum() == 7000
    assert panel["abatement_amount"].sum() == 800.5
    proxy_rows = panel[panel["category_5"].eq("tax_benefit_intent_proxy")]
    assert proxy_rows["manual_review_required"].all()
    pluto = panel[panel["source_dataset_key"].eq("dcp_pluto")].iloc[0]
    assert pluto["borough"] == "MANHATTAN"
    assert pluto["unit_count"] == 750

    result = nyc_reg_builder.emit(
        panel,
        stats,
        tmp_path / "nyc_rent_regulation_tax_benefit_panel.parquet",
        datetime(2026, 6, 28, tzinfo=timezone.utc),
    )
    manifest = nyc_reg_builder.write_manifest(result, tmp_path / "manifests", "2026-06-28T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "nyc_rent_regulation_tax_benefit_panel"
