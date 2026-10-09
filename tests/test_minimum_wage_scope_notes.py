"""Guard the public wording around frozen effective-floor calibration runs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "pcw100_us_mw_increase_event_"


def test_scope_notes_cover_the_exact_public_family() -> None:
    registry = json.loads((ROOT / "engine/public_evidence_scope_notes.json").read_text())
    assert registry["schema"] == "ieset-public-evidence-scope-notes-v1"
    actual = [hypothesis_id for row in registry["notes"] for hypothesis_id in row["hypothesis_ids"]]
    expected = sorted(path.stem for path in (ROOT / "hypotheses").rglob(f"{PREFIX}*.yaml"))
    assert len(actual) == len(set(actual)) == 10
    assert sorted(actual) == expected
    for row in registry["notes"]:
        note = row["note"].lower()
        assert "federal floor" in note
        assert "effective" in note
        assert "state law" in note
        assert "causal" in note


def test_frozen_frame_scope_count() -> None:
    panel = pd.read_parquet(ROOT / "data/derived/us_state_minimum_wage_treatment_panel.parquet")
    panel = panel[panel["year"].between(2006, 2024) & ~panel["state_abbr"].isin({"GU", "PR", "VI"})]
    positives = panel[panel["minimum_wage_increase"] > 0.001]
    federal_only = positives[~positives["binds_above_federal"]]
    assert len(panel) == 969
    assert len(positives) == 419
    assert len(federal_only) == 71
    assert federal_only.groupby("year").size().to_dict() == {2008: 18, 2009: 23, 2010: 30}
