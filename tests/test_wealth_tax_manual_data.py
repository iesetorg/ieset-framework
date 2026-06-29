"""Validate the curated wealth-tax forecast-vs-realized panel.

This guards the manual CSV that unblocks
`wealth_tax_capital_flight_revenue_yield_gap`. It asserts the file loads via
the production fetcher, that every required column is present and non-empty,
that forecast/realized revenue are numeric and positive, that every row carries
a source_url, and that at least three distinct countries are covered.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data.fetchers import wealth_tax_manual  # noqa: E402

REQUIRED = wealth_tax_manual.REQUIRED
CSV = wealth_tax_manual.INPUT


def _frame() -> pd.DataFrame:
    return pd.read_csv(CSV, dtype={"country_iso3": "string", "case_id": "string"})


def test_csv_exists():
    assert CSV.exists(), f"missing curated panel at {CSV}"


def test_fetcher_loads_and_writes_vintage():
    result = wealth_tax_manual.fetch()
    assert result.rows >= 6, "spec wants >=6 well-cited rows"
    assert Path(result.parquet_path).exists()
    assert len(result.sha256) == 64
    assert result.frequency == "annual"


def test_required_columns_present_and_nonempty():
    df = _frame()
    for col in REQUIRED:
        assert col in df.columns, f"missing required column {col!r}"
    for col in REQUIRED:
        assert df[col].notna().all(), f"column {col!r} has empty cells"
        assert (df[col].astype(str).str.strip().str.len() > 0).all(), f"column {col!r} has blank cells"


def test_forecast_and_realized_numeric_and_positive():
    df = _frame()
    for col in ("forecast_revenue_local", "realized_revenue_local"):
        vals = pd.to_numeric(df[col], errors="coerce")
        assert vals.notna().all(), f"{col} must be fully numeric"
        assert (vals > 0).all(), f"{col} must be strictly positive"


def test_years_are_integers_and_plausible():
    df = _frame()
    for col in ("forecast_vintage_year", "revenue_year"):
        vals = pd.to_numeric(df[col], errors="coerce")
        assert vals.notna().all()
        assert vals.between(1980, 2030).all(), f"{col} out of plausible range"
    # A forecast is made no later than the revenue year it projects.
    assert (
        pd.to_numeric(df["forecast_vintage_year"]) <= pd.to_numeric(df["revenue_year"])
    ).all(), "forecast vintage must precede or equal revenue year"


def test_every_row_has_a_source_url():
    df = _frame()
    src = df["source_url"].astype(str)
    assert (src.str.startswith("http")).all(), "every row needs an http(s) source_url"
    assert (src.str.len() >= 8).all()
    meth = df["methodology_url"].astype(str)
    assert (meth.str.startswith("http")).all(), "every row needs an http(s) methodology_url"


def test_at_least_three_distinct_countries():
    df = _frame()
    countries = set(df["country_iso3"].dropna().unique())
    assert len(countries) >= 3, f"need >=3 countries, got {sorted(countries)}"
    # The four preregistered treated countries for the hypothesis.
    assert {"FRA", "NOR", "ESP"}.issubset(countries) or {"FRA", "ESP", "COL"}.issubset(countries)


def test_currency_matches_country():
    df = _frame()
    expected = {"FRA": "EUR", "ESP": "EUR", "NOR": "NOK", "COL": "COP"}
    for _, row in df.iterrows():
        c = row["country_iso3"]
        if c in expected:
            assert row["currency"] == expected[c], f"{c} should be {expected[c]}, got {row['currency']}"
