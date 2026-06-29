from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_sweden_scb_municipal_housing_panel as sweden_builder  # noqa: E402


def test_sweden_scb_panel_flattens_jsonstat_and_matches_top1000_cities(tmp_path: Path):
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

    rent_payload = {
        "id": ["Region", "Hyresuppg", "ContentsCode", "Tid"],
        "size": [2, 1, 1, 1],
        "label": "Average rent in rented dwelling by region, rental data, observations and year",
        "updated": "2025-10-03T06:00:00Z",
        "dimension": {
            "Region": {
                "category": {
                    "index": {"0180": 0, "1480": 1},
                    "label": {"0180": "Stockholm", "1480": "Göteborg"},
                }
            },
            "Hyresuppg": {
                "category": {
                    "index": {"Ah_kvm": 0},
                    "label": {"Ah_kvm": "Annual rent per square metre"},
                }
            },
            "ContentsCode": {
                "category": {
                    "index": {"000000RZ": 0},
                    "label": {"000000RZ": "Average rent in rented dwelling "},
                    "unit": {"000000RZ": {"base": "SEK", "decimals": 0}},
                }
            },
            "Tid": {"category": {"index": {"2025": 0}, "label": {"2025": "2025"}}},
        },
        "value": [1734, 1536],
    }
    completion_payload = {
        "id": ["Region", "Hustyp", "Upplatelseform", "ContentsCode", "Tid"],
        "size": [1, 1, 1, 1, 1],
        "label": "Completed dwellings by region, type of building, tenure, observations and year",
        "updated": "2026-05-11T06:00:00Z",
        "dimension": {
            "Region": {"category": {"index": {"0180": 0}, "label": {"0180": "Stockholm"}}},
            "Hustyp": {"category": {"index": {"FLERBO": 0}, "label": {"FLERBO": "multi-dwelling buildings"}}},
            "Upplatelseform": {"category": {"index": {"1": 0}, "label": {"1": "rented dwellings"}}},
            "ContentsCode": {
                "category": {
                    "index": {"0000005O": 0},
                    "label": {"0000005O": "Number"},
                    "unit": {"0000005O": {"base": "number", "decimals": 0}},
                }
            },
            "Tid": {"category": {"index": {"2025": 0}, "label": {"2025": "2025"}}},
        },
        "value": [321],
    }

    panel, stats = sweden_builder.build_panel(
        city_spine_path=spine,
        payloads=[
            {"table_key": "municipal_rent_per_sqm", "payload": rent_payload},
            {"table_key": "completed_new_dwellings", "payload": completion_payload},
        ],
    )

    assert len(panel) == 3
    assert stats["unique_ieset_city_ids"] == 2
    assert stats["rent_rows"] == 2
    assert stats["completion_rows"] == 1
    assert stats["completed_new_dwellings"] == 321

    stockholm_rent = panel[panel["region_code"].eq("0180") & panel["measure"].eq("municipal_rent_per_sqm")].iloc[0]
    assert stockholm_rent["ieset_city_id"] == "ghsl_ucdb_r2024a:1693"
    assert stockholm_rent["measure_statistic"] == "average"
    assert stockholm_rent["unit"] == "SEK"
    assert stockholm_rent["value"] == 1734

    gothenburg = panel[panel["region_code"].eq("1480")].iloc[0]
    assert gothenburg["ieset_city_id"] == "ghsl_ucdb_r2024a:75"
    assert gothenburg["ghsl_city_name"] == "Gothenburg"

    result = sweden_builder.emit(
        panel,
        stats,
        tmp_path / "sweden_scb_municipal_housing_panel.parquet",
        datetime(2026, 6, 29, tzinfo=timezone.utc),
    )
    manifest = sweden_builder.write_manifest(result, tmp_path / "manifests", "2026-06-29T000000Z")
    payload = yaml.safe_load(manifest.read_text())
    assert payload["entries"][0]["series_id"] == "sweden_scb_municipal_housing_panel"
