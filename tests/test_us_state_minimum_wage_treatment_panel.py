"""Acceptance tests for the U.S. state minimum-wage treatment panel."""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "derived" / "us_state_minimum_wage_treatment_panel.parquet"
MW_HISTORY_GLOB = "data/vintages/usdol/state_minimum_wage_history@*.parquet"


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not OUTPUT.exists():
        pytest.skip(f"panel not built yet: {OUTPUT}")
    return pd.read_parquet(OUTPUT)


def _newest(pattern: str) -> Path:
    matches = sorted(glob.glob(str(ROOT / pattern)))
    assert matches, f"no input matched {pattern}"
    return Path(matches[-1])


def test_file_exists() -> None:
    assert OUTPUT.exists(), f"missing output panel: {OUTPUT}"


def test_required_columns(panel: pd.DataFrame) -> None:
    required = {
        "ieset_state_id",
        "unit_id",
        "state_fips",
        "year",
        "effective_minimum_wage",
        "state_statutory_minimum_wage",
        "federal_minimum_wage",
        "binds_above_federal",
        "bite_ratio",
        "minimum_wage_increase",
        "event_type",
        "is_first_bind_event",
        "first_year_binds_above_federal",
        "nominal_real_note",
    }
    missing = required - set(panel.columns)
    assert not missing, f"missing columns: {missing}"


def test_grain_uniqueness(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(["ieset_state_id", "year"]).any()


def test_ieset_state_id_present(panel: pd.DataFrame) -> None:
    assert panel["ieset_state_id"].notna().all()
    assert (panel["unit_id"] == panel["ieset_state_id"]).all()


def test_effective_at_least_federal(panel: pd.DataFrame) -> None:
    assert (panel["effective_minimum_wage"] >= panel["federal_minimum_wage"]).all()


def test_effective_is_max_of_statutory_and_federal(panel: pd.DataFrame) -> None:
    has_stat = panel["state_statutory_minimum_wage"].notna()
    expected = panel.loc[has_stat, ["state_statutory_minimum_wage", "federal_minimum_wage"]].max(axis=1)
    assert (panel.loc[has_stat, "effective_minimum_wage"] == expected).all()
    # Where no statutory rate exists, effective collapses to federal.
    assert (
        panel.loc[~has_stat, "effective_minimum_wage"]
        == panel.loc[~has_stat, "federal_minimum_wage"]
    ).all()


def test_binds_above_federal_consistency(panel: pd.DataFrame) -> None:
    binding = panel["binds_above_federal"]
    # Where flagged True, statutory must strictly exceed federal.
    assert (panel.loc[binding, "state_statutory_minimum_wage"] > panel.loc[binding, "federal_minimum_wage"]).all()
    # Where flagged False, statutory must NOT exceed federal (or be NaN).
    not_binding = panel.loc[~binding]
    ok = not_binding["state_statutory_minimum_wage"].isna() | (
        not_binding["state_statutory_minimum_wage"] <= not_binding["federal_minimum_wage"]
    )
    assert ok.all()


def test_bite_ratio_present_for_joined_rows(panel: pd.DataFrame) -> None:
    # At least some rows carry a bite ratio (the join produced matches).
    assert panel["bite_ratio"].notna().sum() > 0
    # Every bite-ratio row is within the bite panel's year coverage and finite.
    rows = panel[panel["bite_ratio"].notna()]
    assert (rows["bite_ratio"] > 0).all()


def test_no_fabricated_future_years(panel: pd.DataFrame) -> None:
    mw = pd.read_parquet(_newest(MW_HISTORY_GLOB))
    assert panel["year"].max() <= int(mw["year"].max())
    assert set(panel["year"]).issubset(set(mw["year"].unique()))


def test_first_bind_event_coding(panel: pd.DataFrame) -> None:
    # Every state that ever binds above federal has exactly one first_bind event,
    # and it occurs at that state's minimum binding year.
    binding = panel[panel["binds_above_federal"]]
    for sid, grp in binding.groupby("ieset_state_id"):
        first_year = grp["year"].min()
        events = panel[(panel["ieset_state_id"] == sid) & (panel["event_type"] == "first_bind")]
        assert len(events) == 1, f"{sid} has {len(events)} first_bind events"
        assert int(events["year"].iloc[0]) == int(first_year)
        assert bool(events["is_first_bind_event"].iloc[0]) is True


def test_minimum_wage_increase_matches_diff(panel: pd.DataFrame) -> None:
    p = panel.sort_values(["ieset_state_id", "year"])
    expected = p.groupby("ieset_state_id")["effective_minimum_wage"].diff()
    pd.testing.assert_series_equal(
        p["minimum_wage_increase"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )
