from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_state_level_source_index as state_index  # noqa: E402
import validate_state_level_sources as validate_sources  # noqa: E402


def test_cross_reference_errors_catches_unknown_queue_source():
    inventory = {
        "canonical_state_universe": {"preferred_anchor": "geoboundaries_admin1"},
        "source_records": [{"source_id": "geoboundaries_admin1"}],
    }
    queue = {
        "waves": [
            {
                "wave_id": "state_spine_v0",
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


def test_state_level_index_builds_expected_summary():
    payload = state_index.build_index()

    assert payload["summary"]["source_count"] >= 50
    assert payload["summary"]["wave_count"] == 6
    assert payload["summary"]["preferred_state_anchor"] == "geoboundaries_admin1"
    assert payload["top_ingestion_candidates"][0]["source_id"] == "geoboundaries_admin1"
    assert any(wave["wave_id"] == "us_state_labor_policy_v0" for wave in payload["waves"])
