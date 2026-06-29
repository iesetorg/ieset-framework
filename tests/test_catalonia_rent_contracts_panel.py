from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_catalonia_rent_contracts_panel as catalonia_builder  # noqa: E402


def test_catalonia_rent_contracts_panel_normalizes_rows_and_matches_barcelona(tmp_path: Path):
    spine = tmp_path / "city_universe_top1000.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:5071",
                "city_rank_2025": 118,
                "city_name": "Barcelona",
                "country_name": "Spain",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3338",
                "city_rank_2025": 72,
                "city_name": "Madrid",
                "country_name": "Spain",
            },
        ]
    ).to_parquet(spine, index=False)

    rows = [
        {
            "Any": "2024",
            "Trimestre": "1",
            "Codi municipi": "08019",
            "Nom municipi": "Barcelona",
            "Nombre contractes": "10.000",
            "Lloguer mitja mensual": "1.234,50",
            "Lloguer mitja per m2": "17,2",
        },
        {
            "Any": "2024",
            "Trimestre": "1",
            "Codi municipi": "17079",
            "Nom municipi": "Girona",
            "Nombre contractes": "500",
            "Lloguer mitja mensual": "850,00",
            "Lloguer mitja per m2": "11,4",
        },
    ]

    panel, stats = catalonia_builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 2
    assert stats["matched_municipalities"] == 1
    assert stats["unique_ieset_city_ids"] == 1
    barcelona = panel[panel["municipality_name"].eq("Barcelona")].iloc[0]
    assert barcelona["ieset_city_id"] == "ghsl_ucdb_r2024a:5071"
    assert barcelona["period"] == "2024Q1"
    assert barcelona["contracts"] == 10000
    assert barcelona["avg_monthly_rent_eur"] == 1234.5
    assert barcelona["avg_rent_per_m2_eur"] == 17.2
    girona = panel[panel["municipality_name"].eq("Girona")].iloc[0]
    assert pd.isna(girona["ieset_city_id"])
    assert girona["manual_review_required"]

    result = catalonia_builder.emit(
        panel,
        stats,
        tmp_path / "catalonia_rent_contracts_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = catalonia_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "catalonia_rent_contracts_panel"
