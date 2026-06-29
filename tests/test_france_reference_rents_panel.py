from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_france_reference_rents_panel as france_builder  # noqa: E402


def test_france_reference_rents_panel_normalizes_policy_cells_and_matches_paris(tmp_path: Path):
    spine = tmp_path / "city_universe_top1000.parquet"
    pd.DataFrame(
        [
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:2878",
                "city_rank_2025": 40,
                "city_name": "Paris",
                "country_name": "France",
            },
            {
                "ieset_city_id": "ghsl_ucdb_r2024a:3449",
                "city_rank_2025": 587,
                "city_name": "Lille",
                "country_name": "France",
            },
        ]
    ).to_parquet(spine, index=False)

    rows = [
        {
            "annee": "2024",
            "ville": "Paris",
            "id_zone": "1",
            "nom_quartier": "Saint-Germain-l'Auxerrois",
            "piece": "2",
            "epoque": "Avant 1946",
            "meuble_txt": "Non meuble",
            "ref": "28,3",
            "max": "34,0",
            "min": "19,8",
        },
        {
            "annee": "2024",
            "ville": "Lomme",
            "id_zone": "A",
            "nom_quartier": "Lomme",
            "piece": "1",
            "epoque": "Apres 1990",
            "meuble_txt": "Meuble",
            "ref": "14.2",
            "max": "17.0",
            "min": "10.0",
        },
    ]

    panel, stats = france_builder.build_panel(city_spine_path=spine, rows=rows)

    assert len(panel) == 2
    assert stats["matched_cities"] == 2
    paris = panel[panel["city_name"].eq("Paris")].iloc[0]
    assert paris["ieset_city_id"] == "ghsl_ucdb_r2024a:2878"
    assert paris["rooms"] == 2
    assert paris["reference_rent_eur_m2"] == 28.3
    assert paris["ceiling_rent_eur_m2"] == 34.0
    assert paris["rent_ceiling_multiplier"] == pytest.approx(34.0 / 28.3)
    lomme = panel[panel["city_name"].eq("Lomme")].iloc[0]
    assert lomme["ieset_city_id"] == "ghsl_ucdb_r2024a:3449"
    assert lomme["match_type"] == "normalized_name"

    result = france_builder.emit(
        panel,
        stats,
        tmp_path / "france_reference_rents_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = france_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "france_reference_rents_panel"
