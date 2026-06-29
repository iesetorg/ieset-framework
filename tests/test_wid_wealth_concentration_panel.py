"""Tests for the WID wealth-concentration country-year panel.

Asserts schema, non-empty coverage for >=10 countries, plausible value ranges
(shares in 0-100; US top-1% wealth share rises post-1980), and no all-null
columns. Builds the panel on demand if the derived parquet is absent.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "derived" / "wid_wealth_concentration_panel.parquet"
BUILD = ROOT / "scripts" / "build_wid_wealth_concentration_panel.py"

EXPECTED_COLUMNS = {"country_iso3", "year", "series_id", "value", "unit"}
SHARE_SERIES = {
    "top1_net_personal_wealth_share",
    "top01_net_personal_wealth_share",
    "top10_net_personal_wealth_share",
}
RATIO_SERIES = "net_personal_wealth_income_ratio"


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PARQUET.exists():
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        runpy.run_path(str(BUILD), run_name="__main__")
    return pd.read_parquet(PARQUET)


def test_schema_columns_present(panel: pd.DataFrame) -> None:
    assert EXPECTED_COLUMNS.issubset(set(panel.columns)), panel.columns.tolist()


def test_non_empty(panel: pd.DataFrame) -> None:
    assert len(panel) > 0


def test_no_all_null_columns(panel: pd.DataFrame) -> None:
    for col in EXPECTED_COLUMNS:
        assert panel[col].notna().any(), f"column {col} is entirely null"
    assert panel["value"].notna().all(), "value column has nulls"


def test_country_coverage_at_least_ten(panel: pd.DataFrame) -> None:
    assert panel["country_iso3"].nunique() >= 10


def test_all_target_series_present(panel: pd.DataFrame) -> None:
    series = set(panel["series_id"].unique())
    assert SHARE_SERIES.issubset(series)
    assert RATIO_SERIES in series


def test_iso3_codes_are_three_letters(panel: pd.DataFrame) -> None:
    codes = panel["country_iso3"].astype(str)
    assert (codes.str.len() == 3).all()
    assert codes.str.isupper().all()


def test_year_range_plausible(panel: pd.DataFrame) -> None:
    assert panel["year"].min() >= 1980
    assert panel["year"].max() <= 2023


def test_share_values_in_0_100(panel: pd.DataFrame) -> None:
    shares = panel[panel["series_id"].isin(SHARE_SERIES)]["value"]
    assert shares.min() >= 0.0
    assert shares.max() <= 100.0


def test_top_share_ordering(panel: pd.DataFrame) -> None:
    # Top 10% share must be >= top 1% share >= top 0.1% share, per country-year.
    wide = (
        panel[panel["series_id"].isin(SHARE_SERIES)]
        .pivot_table(index=["country_iso3", "year"], columns="series_id", values="value")
        .dropna()
    )
    assert (wide["top10_net_personal_wealth_share"] >= wide["top1_net_personal_wealth_share"]).all()
    assert (wide["top1_net_personal_wealth_share"] >= wide["top01_net_personal_wealth_share"]).all()


def test_ratio_values_positive_and_plausible(panel: pd.DataFrame) -> None:
    ratio = panel[panel["series_id"] == RATIO_SERIES]["value"]
    assert ratio.min() > 0
    # Net personal wealth / national income: plausibly 50%-1500% of nat. income.
    assert ratio.max() <= 1500.0
    assert ratio.median() >= 100.0


def test_us_top1_wealth_share_rises_post_1980(panel: pd.DataFrame) -> None:
    us = panel[
        (panel["country_iso3"] == "USA")
        & (panel["series_id"] == "top1_net_personal_wealth_share")
    ].set_index("year")["value"]
    assert 1980 in us.index
    assert us.index.max() >= 2018
    early = us.loc[1980]
    late = us.loc[us.index.max()]
    assert late > early, f"US top-1% wealth share did not rise: {early} -> {late}"
    # The Saez-Zucman Z2 magnitude: a rise of at least ~5 percentage points.
    assert (late - early) >= 5.0


def test_us_wealth_income_ratio_rises_post_1980(panel: pd.DataFrame) -> None:
    us = panel[
        (panel["country_iso3"] == "USA") & (panel["series_id"] == RATIO_SERIES)
    ].set_index("year")["value"]
    assert us.loc[us.index.max()] > us.loc[1980]
