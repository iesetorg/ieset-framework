from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_second_order_data_index as data_index  # noqa: E402
import validate_second_order_data_program as validate_program  # noqa: E402


def test_cross_reference_errors_catches_unknown_queue_source():
    inventory = {
        "source_records": [
            {
                "source_id": "known_source",
                "source_family_id": "household_distributional_microdata",
                "immediate_payoff_rank": 1,
            }
        ]
    }
    queue = {
        "waves": [
            {
                "wave_id": "bad_wave",
                "source_ids": ["missing_source"],
                "source_family_ids": ["household_distributional_microdata"],
            }
        ]
    }

    errors = validate_program.cross_reference_errors(
        inventory,
        queue,
        {"household_distributional_microdata"},
    )

    assert any("unknown source_id 'missing_source'" in err for err in errors)


def test_cross_reference_errors_accepts_current_program():
    inventory = validate_program.load_yaml(validate_program.INVENTORY_PATH)
    queue = validate_program.load_yaml(validate_program.QUEUE_PATH)
    family_ids = validate_program.second_order_family_ids()

    assert validate_program.cross_reference_errors(inventory, queue, family_ids) == []


def test_second_order_data_index_builds_expected_summary():
    payload = data_index.build_index()

    assert payload["summary"]["source_count"] >= 20
    assert payload["summary"]["wave_count"] >= 8
    assert payload["summary"]["backlog_snapshot"]["strict_held_public_claim_links"] == 4847
    assert payload["top_ingestion_candidates"][0]["source_id"] == "ieset_policy_event_treatment_contracts"
    assert any(wave["wave_id"] == "treatment_contracts_backfill_v0" for wave in payload["waves"])
    assert "distributional_incidence" in payload["summary"]["second_order_layer_counts"]
