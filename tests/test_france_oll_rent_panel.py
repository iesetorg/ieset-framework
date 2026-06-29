"""Tests for the France OLL observed market-rent panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data" / "derived" / "france_oll_rent_panel.parquet"

GRAIN_KEYS = [
    "observatory_code",
    "agglomeration",
    "data_year",
    "zone_complementaire",
    "dwelling_type",
    "construction_period",
    "tenure_length",
    "rooms_band",
]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL_PATH.exists():
        pytest.skip(f"panel not built: {PANEL_PATH}")
    return pd.read_parquet(PANEL_PATH)


def test_panel_exists():
    assert PANEL_PATH.exists(), f"missing panel artifact: {PANEL_PATH}"


def test_grain_uniqueness(panel: pd.DataFrame):
    key = panel[GRAIN_KEYS].astype(object).where(panel[GRAIN_KEYS].notna(), "__NA__")
    dup = key.duplicated()
    assert not dup.any(), f"{int(dup.sum())} duplicate rows on grain {GRAIN_KEYS}"


def test_rent_per_m2_positive_and_plausible(panel: pd.DataFrame):
    rent = panel["rent_eur_m2_median"].dropna()
    assert not rent.empty, "no rent_eur_m2_median values present"
    assert (rent > 0).all(), "non-positive EUR/m2 rents present"
    # French observed market rents fall well within this band (EUR/m2/month).
    assert rent.between(2, 60).mean() > 0.99, "EUR/m2 rents outside plausible 2-60 band"


def test_monthly_rent_present_and_positive(panel: pd.DataFrame):
    assert "rent_eur_month_median" in panel.columns
    monthly = panel["rent_eur_month_median"].dropna()
    assert not monthly.empty, "no monthly rent values present"
    assert (monthly > 0).all(), "non-positive EUR/month rents present"


def test_ghsl_match_flag_present(panel: pd.DataFrame):
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].dtype == bool or set(panel["ghsl_match_flag"].dropna().unique()) <= {True, False}
    assert panel["ghsl_match_flag"].any(), "no rows matched to GHSL spine"


def test_paris_or_lyon_matched(panel: pd.DataFrame):
    matched = panel.loc[panel["ghsl_match_flag"], "ghsl_city_name"].dropna().unique()
    assert {"Paris", "Lyon"} & set(matched), f"neither Paris nor Lyon matched; matched={sorted(matched)}"


def test_matched_rows_have_city_id(panel: pd.DataFrame):
    matched = panel[panel["ghsl_match_flag"]]
    assert matched["ieset_city_id"].notna().all(), "matched rows missing ieset_city_id"


def test_original_codes_preserved(panel: pd.DataFrame):
    # Original OLL observatory codes + agglomeration labels must survive.
    for col in ("observatory_code", "agglomeration"):
        assert col in panel.columns
    assert panel["observatory_code"].notna().any(), "observatory_code all null"
    assert panel["agglomeration"].notna().all(), "agglomeration label missing"


def test_observed_vs_estimated_labeling(panel: pd.DataFrame):
    assert "rent_measure" in panel.columns
    assert (panel["rent_measure"] == "observed_oll_market_rent").all()
    # Per-cell production method (direct vs econometric) preserved.
    assert "production_method" in panel.columns
    assert panel["production_method"].notna().any(), "production_method all null"
