from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_city_level_sources as validate_sources  # noqa: E402
import generate_city_level_source_index as city_index  # noqa: E402


def test_cross_reference_errors_catches_unknown_queue_source():
    inventory = {
        "canonical_city_universe": {"preferred_anchor": "ghsl_urban_centre_database"},
        "source_records": [{"source_id": "ghsl_urban_centre_database"}],
    }
    queue = {
        "waves": [
            {
                "wave_id": "city_spine_v0",
                "source_ids": ["missing_source"],
                "source_family_ids": [],
            }
        ]
    }

    errors = validate_sources.cross_reference_errors(inventory, queue, set())

    assert any("unknown source_id 'missing_source'" in err for err in errors)


def test_cross_reference_errors_accepts_current_catalog():
    inventory = validate_sources.load_yaml(validate_sources.INVENTORY_PATH)
    queue = validate_sources.load_yaml(validate_sources.QUEUE_PATH)
    family_ids = validate_sources.second_order_family_ids()

    assert validate_sources.cross_reference_errors(inventory, queue, family_ids) == []


def test_city_level_index_builds_expected_summary():
    payload = city_index.build_index()

    assert payload["summary"]["source_count"] >= 80
    assert payload["summary"]["wave_count"] == 7
    assert payload["summary"]["preferred_city_anchor"] == "ghsl_urban_centre_database"
    assert payload["top_ingestion_candidates"][0]["source_id"] == "ghsl_urban_centre_database"
    assert any(wave["wave_id"] == "us_rent_control_pilot_v0" for wave in payload["waves"])
