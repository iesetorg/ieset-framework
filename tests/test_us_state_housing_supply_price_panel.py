"""Tests for the U.S. state housing supply + price panel.

Validates the derived artifact
data/derived/us_state_housing_supply_price_panel.parquet built by
scripts/build_us_state_housing_supply_price_panel.py:

  - the file exists and loads,
  - grain is unique on (ieset_state_id, year),
  - the 50 states + DC are all present for a recent BPS year,
  - permit counts are non-negative,
  - per-structure-type permits sum to the BPS total (within rounding),
  - the FHFA HPI index is strictly positive where present,
  - state_fips and state_abbr are preserved and consistent with the spine,
  - no fabricated future years (nothing beyond the current calendar year).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data" / "derived" / "us_state_housing_supply_price_panel.parquet"
SPINE_PATH = ROOT / "data" / "derived" / "state_universe_admin1.parquet"

STRUCTURE_COLS = [
    "bps_units_1_unit",
    "bps_units_2_to_4_unit",
    "bps_units_5_plus_unit",
]
PERMIT_COLS = ["bps_total_permit_units", *STRUCTURE_COLS, "bps_reported_total_permit_units"]

# 50 states + DC postal abbreviations (DC is a federal district but is the
# 51st canonical state-equivalent and is covered by both BPS and FHFA).
STATES_50_PLUS_DC = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI",
    "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN",
    "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA",
    "WV", "WI", "WY",
}


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
        "bps_total_permit_units",
        "bps_units_1_unit",
        "bps_units_2_to_4_unit",
        "bps_units_5_plus_unit",
        "fhfa_hpi_at_index",
    }
    assert expected.issubset(set(panel.columns))


def test_grain_unique_on_state_year(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(["ieset_state_id", "year"]).any()


def test_50_states_plus_dc_present_recent_year(panel: pd.DataFrame) -> None:
    """All 50 states + DC must have BPS permit data for a recent year."""
    bps = panel[panel["bps_total_permit_units"].notna()]
    recent_year = int(bps["year"].max())
    abbrs_recent = set(
        panel.loc[
            (panel["year"] == recent_year) & (panel["bps_total_permit_units"].notna()),
            "state_abbr",
        ]
    )
    missing = STATES_50_PLUS_DC - abbrs_recent
    assert not missing, f"missing states for {recent_year}: {sorted(missing)}"
    assert len(STATES_50_PLUS_DC) == 51


def test_permits_non_negative(panel: pd.DataFrame) -> None:
    for col in PERMIT_COLS:
        vals = panel[col].dropna()
        assert (vals >= 0).all(), f"negative permit values in {col}"


def test_structure_types_sum_to_total(panel: pd.DataFrame) -> None:
    """1-unit + 2-4 unit + 5+ unit must equal the BPS total within rounding."""
    sub = panel.dropna(subset=["bps_total_permit_units", *STRUCTURE_COLS]).copy()
    assert len(sub) > 0
    calc = sub[STRUCTURE_COLS].sum(axis=1)
    diff = (calc - sub["bps_total_permit_units"]).abs()
    # Components and total are integer unit counts; allow a tiny rounding margin.
    assert (diff <= 1).all(), f"max structure-sum deviation {diff.max()}"


def test_fhfa_index_positive(panel: pd.DataFrame) -> None:
    idx = panel["fhfa_hpi_at_index"].dropna()
    assert len(idx) > 0
    assert (idx > 0).all()


def test_state_fips_and_abbr_preserved(panel: pd.DataFrame) -> None:
    assert panel["state_fips"].notna().all()
    assert panel["state_abbr"].notna().all()
    # 2-digit zero-padded FIPS, 2-letter uppercase abbreviations.
    assert panel["state_fips"].astype(str).str.fullmatch(r"\d{2}").all()
    assert panel["state_abbr"].astype(str).str.fullmatch(r"[A-Z]{2}").all()
    # Consistency with the canonical spine abbr<->FIPS mapping.
    spine = pd.read_parquet(SPINE_PATH)[["state_abbr", "state_fips"]].copy()
    spine["state_fips"] = spine["state_fips"].astype(str).str.zfill(2)
    spine["state_abbr"] = spine["state_abbr"].astype(str).str.upper()
    spine_map = dict(zip(spine["state_abbr"], spine["state_fips"]))
    for abbr, fips in panel[["state_abbr", "state_fips"]].drop_duplicates().itertuples(index=False):
        assert spine_map.get(abbr) == fips, f"{abbr} fips mismatch: {fips} != {spine_map.get(abbr)}"


def test_no_fabricated_future_years(panel: pd.DataFrame) -> None:
    current_year = datetime.now(tz=timezone.utc).year
    assert int(panel["year"].max()) <= current_year
    # Any year at the current calendar year that carries FHFA data must be
    # flagged as a partial (incomplete) year rather than presented as complete.
    cur = panel[(panel["year"] == current_year) & panel["fhfa_hpi_at_index"].notna()]
    if len(cur) > 0:
        assert bool(cur["fhfa_hpi_partial_year"].all())
