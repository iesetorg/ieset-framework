"""Synthetic check of the documented out-of-roster WDI duplicate repair."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts/run_wdi_tourism_response_six_outcome_2026.py"
SPEC = importlib.util.spec_from_file_location("wdi_tourism_response_parser_erratum", RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def source_rows(path, columns, duplicate_within_roster=False):
    assert columns == ["country_iso3", "indicator_id", "year", "value", "obs_status"]
    series_id = Path(path).name.split("@")[0]
    rows = [
        ("", series_id, 1960, 1.0, None),
        ("", series_id, 1960, 2.0, None),
        ("USA", series_id, 2007, 3.0, "A"),
        ("USA", series_id, 2020, 4.0, "A"),
    ]
    if duplicate_within_roster:
        rows.append(("USA", series_id, 2007, 5.0, "A"))
    return pd.DataFrame(rows, columns=columns)


def test_outside_roster_and_year_duplicates_are_ignored(monkeypatch):
    monkeypatch.setattr(runner.pd, "read_parquet", source_rows)
    loaded = runner.load_sources()
    assert set(loaded) == set(runner.SOURCES)
    for role in runner.SOURCES:
        assert loaded[role] == {("USA", 2007): (3.0, "A")}


def test_inside_roster_duplicate_still_fails(monkeypatch):
    monkeypatch.setattr(
        runner.pd, "read_parquet",
        lambda path, columns: source_rows(path, columns, duplicate_within_roster=True),
    )
    with pytest.raises(RuntimeError, match="duplicate WDI country-year: arrivals/\\('USA', 2007\\)"):
        runner.load_sources()
