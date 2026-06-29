"""Tests for the U.S. state-government fiscal panel.

Validates the derived artifact
data/derived/us_state_gov_finances_panel.parquet built by
scripts/build_us_state_gov_finances_panel.py (Census Annual Survey of State &
Local Government Finances, state-government-total level of estimate):

  - the file exists and loads with the expected headline columns,
  - grain is unique on (ieset_state_id, year),
  - the 50 states + DC are all present for a recent survey year (territories
    are allowed to be absent — the survey covers state governments only),
  - revenue and expenditure are non-negative,
  - a fiscal-year period field is present and marks every row as fiscal-year,
  - state_fips is preserved and consistent with the canonical spine,
  - no fabricated future years (nothing beyond the current calendar year).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data" / "derived" / "us_state_gov_finances_panel.parquet"
SPINE_PATH = ROOT / "data" / "derived" / "state_universe_admin1.parquet"

# 50 states + DC postal abbreviations. The gov-finances survey covers state
# governments; DC is treated as a state-equivalent. Territories are not in the
# state-by-level-of-estimate file and may legitimately be absent.
STATES_50_PLUS_DC = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
    "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY",
}

NON_NEGATIVE_COLS = [
    "total_revenue",
    "total_expenditure",
    "total_tax_revenue",
    "intergovernmental_revenue",
    "total_debt_outstanding",
]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    assert PANEL_PATH.exists(), f"missing panel artifact: {PANEL_PATH}"
    return pd.read_parquet(PANEL_PATH)


def test_file_exists_and_loads(panel: pd.DataFrame) -> None:
    assert len(panel) > 0
    expected = {
        "ieset_state_id",
        "state_fips",
        "state_abbr",
        "state_name",
        "year",
        "period_type",
        "fiscal_year",
        "total_revenue",
        "total_expenditure",
        "total_tax_revenue",
        "intergovernmental_revenue",
        "total_debt_outstanding",
        "individual_income_tax",
        "corporate_income_tax",
    }
    assert expected.issubset(set(panel.columns)), (
        f"missing columns: {expected - set(panel.columns)}"
    )


def test_grain_unique_on_state_year(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(["ieset_state_id", "year"]).any()


def test_50_states_plus_dc_present_recent_year(panel: pd.DataFrame) -> None:
    """All 50 states + DC must have fiscal data for a recent survey year."""
    has_rev = panel[panel["total_revenue"].notna()]
    recent_year = int(has_rev["year"].max())
    abbrs_recent = set(
        panel.loc[
            (panel["year"] == recent_year) & (panel["total_revenue"].notna()),
            "state_abbr",
        ]
    )
    missing = STATES_50_PLUS_DC - abbrs_recent
    assert not missing, f"missing states for {recent_year}: {sorted(missing)}"
    assert len(STATES_50_PLUS_DC) == 51


def test_revenue_expenditure_non_negative(panel: pd.DataFrame) -> None:
    for col in NON_NEGATIVE_COLS:
        vals = panel[col].dropna()
        assert (vals >= 0).all(), f"negative values in {col}"


def test_fiscal_year_period_field_present(panel: pd.DataFrame) -> None:
    assert "period_type" in panel.columns
    assert "fiscal_year" in panel.columns
    # The survey is fiscal-year: every row must be marked as such.
    assert (panel["period_type"] == "fiscal_year").all()
    # fiscal_year mirrors the survey reference year.
    assert (panel["fiscal_year"].astype(int) == panel["year"].astype(int)).all()


def test_state_fips_preserved(panel: pd.DataFrame) -> None:
    assert panel["state_fips"].notna().all()
    assert panel["state_fips"].astype(str).str.fullmatch(r"\d{2}").all()
    # Consistency with the canonical spine FIPS<->id mapping.
    spine = pd.read_parquet(SPINE_PATH)[["ieset_state_id", "state_fips"]].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    spine_map = dict(zip(spine["ieset_state_id"], spine["state_fips"]))
    for sid, fips in panel[["ieset_state_id", "state_fips"]].drop_duplicates().itertuples(index=False):
        assert spine_map.get(sid) == fips, f"{sid} fips mismatch: {fips} != {spine_map.get(sid)}"


def test_no_fabricated_future_years(panel: pd.DataFrame) -> None:
    current_year = datetime.now(tz=timezone.utc).year
    assert int(panel["year"].max()) <= current_year
