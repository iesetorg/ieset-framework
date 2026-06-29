"""Tests for the Italy OMI assessor rent-quotation panel."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "derived" / "italy_omi_rent_panel.parquet"

GRAIN_KEYS = ["comune_istat_code", "omi_link_zona", "semester_label", "cod_tipologia", "stato_conservativo"]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    if not PANEL.exists():
        pytest.skip(f"panel not built: {PANEL}")
    return pd.read_parquet(PANEL)


def test_panel_exists_and_nonempty(panel: pd.DataFrame) -> None:
    assert PANEL.exists()
    assert len(panel) > 0


def test_grain_uniqueness(panel: pd.DataFrame) -> None:
    assert not panel.duplicated(subset=GRAIN_KEYS).any()


def test_rent_midpoints_positive_and_plausible(panel: pd.DataFrame) -> None:
    mids = panel["rent_mid_eur_m2_month"].dropna()
    assert len(mids) > 0
    assert (mids > 0).all()
    # OMI rent quotations are EUR/m2/month; bands sit well under ~200.
    assert mids.max() < 200
    assert mids.median() < 60


def test_rent_min_le_max(panel: pd.DataFrame) -> None:
    both = panel.dropna(subset=["rent_min_eur_m2_month", "rent_max_eur_m2_month"])
    assert (both["rent_min_eur_m2_month"] <= both["rent_max_eur_m2_month"]).all()


def test_ghsl_match_flag_present(panel: pd.DataFrame) -> None:
    assert "ghsl_match_flag" in panel.columns
    assert panel["ghsl_match_flag"].notna().all()
    # Unmatched comuni are retained.
    assert (~panel["ghsl_match_flag"]).any()


def test_rome_or_milan_matched(panel: pd.DataFrame) -> None:
    matched = panel[panel["ghsl_match_flag"] == True]  # noqa: E712
    names = set(matched["ghsl_city_name"].dropna())
    assert {"Rome", "Milan"} & names
    assert matched["ieset_city_id"].notna().all()


def test_original_italian_codes_preserved(panel: pd.DataFrame) -> None:
    for col in ["comune_istat_code", "omi_zona", "omi_link_zona", "cod_tipologia", "descr_tipologia", "regione"]:
        assert col in panel.columns
    # ISTAT codes are preserved verbatim; a tiny handful of source rows omit it.
    istat = panel["comune_istat_code"].astype(str)
    assert (istat.str.len() > 0).mean() > 0.999
    # Rome's OMI ISTAT code is preserved verbatim.
    rome = panel[panel["ghsl_city_name"] == "Rome"]
    assert not rome.empty
    assert rome["comune_istat_code"].eq("12058091").all()


def test_rent_not_conflated_with_sale(panel: pd.DataFrame) -> None:
    # No sale-price (compravendita) columns should leak into the rent panel.
    lowered = {c.lower() for c in panel.columns}
    for forbidden in ("compr", "compravendita", "sale", "price"):
        assert not any(forbidden in c for c in lowered), f"sale field leaked: {forbidden}"
    # Value semantics are explicitly assessor quotation rent bands.
    assert panel["value_type"].eq("assessor_quotation_rent_band").all()
    assert "locazione" in panel["source_dataset"].iloc[0].lower()


def test_semester_format(panel: pd.DataFrame) -> None:
    assert panel["semester_label"].str.match(r"^\d{4}-S[12]$").all()
    assert panel["semester"].isin([1, 2]).all()
