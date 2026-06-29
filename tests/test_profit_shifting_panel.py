"""Tests for the multinational profit-shifting panel (Zucman Z5).

Validates schema, coverage, the presence of known tax havens, plausible signs
(havens show net profit inflow / below-average foreign-firm ETR), and that no
series is entirely null.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "derived" / "profit_shifting_panel.parquet"

EXPECTED_COLUMNS = ["jurisdiction_iso3", "year", "series_id", "value", "unit", "source"]
KNOWN_HAVENS = ["IRL", "LUX", "NLD", "CHE", "SGP", "BMU", "CYM"]


pytestmark = pytest.mark.skipif(
    not PANEL.exists(),
    reason="profit_shifting_panel.parquet not built; run scripts/build_profit_shifting_panel.py",
)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def test_schema(panel: pd.DataFrame) -> None:
    assert list(panel.columns) == EXPECTED_COLUMNS
    assert len(panel) > 0
    assert panel["jurisdiction_iso3"].str.len().eq(3).all()
    assert panel["year"].between(1990, 2030).all()
    assert pd.api.types.is_numeric_dtype(panel["value"])


def test_no_duplicate_observations(panel: pd.DataFrame) -> None:
    dup = panel.duplicated(["jurisdiction_iso3", "year", "series_id", "source"])
    assert not dup.any(), f"{dup.sum()} duplicate (jurisdiction, year, series, source) rows"


def test_minimum_jurisdiction_coverage(panel: pd.DataFrame) -> None:
    assert panel["jurisdiction_iso3"].nunique() >= 15

    # The core TWZ shifted-profits series alone must cover >= 15 jurisdictions.
    twz = panel[panel["series_id"] == "twz_shifted_profits_usd_bn"]
    assert twz["jurisdiction_iso3"].nunique() >= 15


def test_known_havens_present(panel: pd.DataFrame) -> None:
    present = set(panel["jurisdiction_iso3"].unique())
    missing = [h for h in KNOWN_HAVENS if h not in present]
    assert not missing, f"missing known havens: {missing}"


def test_havens_show_net_profit_inflow(panel: pd.DataFrame) -> None:
    """In TWZ, havens book profits shifted IN (negative shifted-profits)."""
    sp = panel[panel["series_id"] == "twz_shifted_profits_usd_bn"]
    for haven in ["IRL", "LUX", "NLD", "CHE", "SGP", "BMU"]:
        vals = sp[sp["jurisdiction_iso3"] == haven]["value"]
        assert len(vals) > 0, f"no shifted-profit value for haven {haven}"
        assert (vals < 0).all(), f"{haven} should show net inflow (negative), got {vals.tolist()}"


def test_high_tax_countries_show_outflow(panel: pd.DataFrame) -> None:
    """Large non-haven economies lose profits (positive shifted-profits)."""
    sp = panel[panel["series_id"] == "twz_shifted_profits_usd_bn"]
    for loser in ["USA", "DEU", "FRA"]:
        vals = sp[(sp["jurisdiction_iso3"] == loser)]["value"]
        assert len(vals) > 0
        assert (vals > 0).all(), f"{loser} should show net outflow (positive)"


def test_foreign_firm_etr_havens_below_core(panel: pd.DataFrame) -> None:
    """Foreign-controlled-firm ETR is far lower in havens than core economies."""
    etr = panel[panel["series_id"] == "twz_foreign_firm_effective_tax_rate"]
    etr = etr.set_index("jurisdiction_iso3")["value"]
    assert etr.loc["IRL"] < 15
    assert etr.loc["LUX"] < 15
    assert etr.loc["USA"] > etr.loc["IRL"]
    assert etr.loc["FRA"] > etr.loc["LUX"]


def test_z5_headline_present_and_plausible(panel: pd.DataFrame) -> None:
    """Z5: ~40% of foreign-controlled MNC profits booked in havens (TWZ ~36%)."""
    share = panel[panel["series_id"] == "twz_share_foreign_profits_shifted_pct"]
    assert len(share) == 1
    pct = float(share["value"].iloc[0])
    assert 30 <= pct <= 45, f"headline shifted share {pct}% outside plausible band"

    shifted = panel[panel["series_id"] == "twz_global_shifted_to_havens_usd_bn"]
    assert float(shifted["value"].iloc[0]) > 500  # ~$616B in 2015


def test_no_all_null_series(panel: pd.DataFrame) -> None:
    for sid, grp in panel.groupby("series_id"):
        assert not grp["value"].isna().all(), f"series {sid} is entirely null"
        assert len(grp) > 0


def test_units_and_sources_populated(panel: pd.DataFrame) -> None:
    assert panel["unit"].notna().all()
    assert panel["source"].notna().all()
    assert panel["source"].str.contains("twz|cbcr", case=False).all()
