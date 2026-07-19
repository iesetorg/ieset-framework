from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROADMAP = (
    ROOT
    / "engine"
    / "audits"
    / "next_200_scoreboard_data_gap_roadmap_2026-07-19.json"
)
BACKLOG = ROOT / "engine" / "second_order_test_backlog.json"


def test_roadmap_is_exactly_the_ranked_next_200():
    roadmap = json.loads(ROADMAP.read_text())
    backlog = json.loads(BACKLOG.read_text())
    candidates = roadmap["candidates"]

    assert len(candidates) == 200
    assert len({row["hypothesis_id"] for row in candidates}) == 200
    assert [row["rank"] for row in candidates] == list(range(1, 201))
    assert [row["hypothesis_id"] for row in candidates] == [
        row["hypothesis_id"] for row in backlog["backlog"][:200]
    ]


def test_roadmap_has_four_complete_execution_waves():
    roadmap = json.loads(ROADMAP.read_text())
    candidates = roadmap["candidates"]

    assert Counter(row["wave"] for row in candidates) == {
        1: 50,
        2: 50,
        3: 50,
        4: 50,
    }
    assert [wave["rank_range"] for wave in roadmap["waves"]] == [
        [1, 50],
        [51, 100],
        [101, 150],
        [151, 200],
    ]


def test_roadmap_reports_unmapped_causal_layers_as_data_gaps():
    roadmap = json.loads(ROADMAP.read_text())
    candidates = roadmap["candidates"]
    source_gap_rows = [
        row for row in candidates if row["acquisition_class"] == "source_family_gap"
    ]

    assert source_gap_rows
    assert all(row["uncovered_layers"] for row in source_gap_rows)
    portfolio_ids = {
        row["family_id"] for row in roadmap["top_200_data_gap_portfolio"]
    }
    for row in source_gap_rows:
        for layer in row["uncovered_layers"]:
            assert f"source_family_gap:{layer}" in portfolio_ids


def test_roadmap_link_exposure_reconciles_to_queue_and_corpus():
    roadmap = json.loads(ROADMAP.read_text())
    backlog = json.loads(BACKLOG.read_text())
    selection = roadmap["selection"]
    queue_links = sum(
        row["public_claim_links_at_gate"] for row in roadmap["candidates"]
    )

    assert selection["queue_held_link_exposure"] == queue_links
    assert (
        selection["whole_corpus_held_public_claim_links"]
        == backlog["summary"]["held_public_claim_links"]
    )
