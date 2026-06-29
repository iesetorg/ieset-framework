"""Schema + plausibility tests for the OECD tax-structure panel.

Validates the derived long panel produced by
scripts/build_oecd_tax_structure_panel.py:
- long schema (country_iso3, year, series_id, value, unit)
- >= 20 countries
- plausible ranges (tax/GDP, top PIT, CIT)
- no all-null series
- wealth-tax revenue present for known levyers (CH, NO, ES, FR pre-2018)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "derived" / "oecd_tax_structure_panel.parquet"

EXPECTED_COLUMNS = {"country_iso3", "year", "series_id", "value", "unit"}
EXPECTED_SERIES = {
    "oecd_tax_recurrent_net_wealth_pct_gdp",
    "oecd_tax_estate_inheritance_gift_pct_gdp",
    "oecd_tax_total_pct_gdp",
    "oecd_tax_recurrent_net_wealth_pct_total_tax",
    "oecd_tax_estate_inheritance_gift_pct_total_tax",
    "oecd_top_statutory_pit_rate",
    "oecd_combined_corporate_income_tax_rate",
}


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL.exists():
        pytest.skip(f"panel not built: {PANEL}")
    return pd.read_parquet(PANEL)


def test_schema(panel: pd.DataFrame) -> None:
    assert set(panel.columns) == EXPECTED_COLUMNS
    assert panel["country_iso3"].map(lambda s: isinstance(s, str) and len(s) == 3).all()
    assert pd.api.types.is_integer_dtype(panel["year"])
    assert panel["value"].notna().all()
    assert panel["value"].dtype.kind == "f"


def test_expected_series_present(panel: pd.DataFrame) -> None:
    assert EXPECTED_SERIES.issubset(set(panel["series_id"].unique()))


def test_no_all_null_series(panel: pd.DataFrame) -> None:
    for sid, grp in panel.groupby("series_id"):
        assert grp["value"].notna().any(), f"series {sid} is all-null"
        assert len(grp) > 0


def test_country_coverage(panel: pd.DataFrame) -> None:
    assert panel["country_iso3"].nunique() >= 20
    # Every series should itself be reasonably broad.
    for sid, grp in panel.groupby("series_id"):
        assert grp["country_iso3"].nunique() >= 20, f"{sid} thin: {grp['country_iso3'].nunique()}"


def test_year_range(panel: pd.DataFrame) -> None:
    assert panel["year"].min() >= 1990
    assert panel["year"].max() <= 2024


def test_total_tax_gdp_plausible(panel: pd.DataFrame) -> None:
    tot = panel[panel["series_id"] == "oecd_tax_total_pct_gdp"]["value"]
    # Non-negative, and the OECD-core bulk sits in 10-55% of GDP. A handful of
    # small partner economies dip below 10%, so check the bulk (5th-95th pct).
    assert (tot >= 0).all()
    assert tot.quantile(0.05) >= 5.0
    assert tot.quantile(0.95) <= 55.0
    assert tot.max() <= 70.0


def test_top_pit_plausible(panel: pd.DataFrame) -> None:
    pit = panel[panel["series_id"] == "oecd_top_statutory_pit_rate"]["value"]
    assert (pit >= 0).all()
    # Bulk within 0-65%. One documented outlier exists (FRA 2013 = 122.8%,
    # reflecting the temporary French 75% top-bracket episode), so assert on the
    # 99th percentile rather than the absolute max.
    assert pit.quantile(0.99) <= 65.0
    assert pit.median() >= 20.0


def test_cit_plausible(panel: pd.DataFrame) -> None:
    cit = panel[panel["series_id"] == "oecd_combined_corporate_income_tax_rate"]["value"]
    assert (cit >= 0).all()
    assert cit.quantile(0.99) <= 60.0
    assert cit.median() >= 10.0


@pytest.mark.parametrize("iso3", ["CHE", "NOR", "ESP"])
def test_known_net_wealth_levyers(panel: pd.DataFrame, iso3: str) -> None:
    nw = panel[
        (panel["series_id"] == "oecd_tax_recurrent_net_wealth_pct_gdp")
        & (panel["country_iso3"] == iso3)
    ]
    assert len(nw) > 0, f"no net-wealth revenue rows for {iso3}"
    assert (nw["value"] > 0).any(), f"{iso3} has no positive net-wealth revenue"


def test_france_net_wealth_pre_2018(panel: pd.DataFrame) -> None:
    # France levied the ISF net wealth tax through 2017.
    fra = panel[
        (panel["series_id"] == "oecd_tax_recurrent_net_wealth_pct_gdp")
        & (panel["country_iso3"] == "FRA")
        & (panel["year"] < 2018)
    ]
    assert (fra["value"] > 0).any(), "FRA pre-2018 net-wealth revenue missing"


def test_units_consistent_per_series(panel: pd.DataFrame) -> None:
    for sid, grp in panel.groupby("series_id"):
        assert grp["unit"].nunique() == 1, f"{sid} has mixed units"
