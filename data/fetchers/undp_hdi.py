"""UNDP Human Development Index (HDI) + components — time-series CSV.

Pulls the Composite Indices Complete Time Series CSV from the 2025 HDR
release. Covers HDI, life expectancy, expected/mean years of schooling,
GNI per capita for 1990-2023 in wide format. Melted to tidy
(country_iso3, year, value) for the target series_id.

Supported series_id values:
    hdi_2025                → composite HDI (0-1 scalar)
    hdi                     → alias for hdi_2025
    life_expectancy         → life expectancy at birth (years)
    mean_years_schooling    → mean years of schooling (years)
    expected_years_schooling → expected years of schooling (years)
    gni_per_capita          → GNI per capita, 2021 PPP $
"""
from __future__ import annotations

import io
import re
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv"
LICENSE = "cc_by_4_0"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}

# Maps series_id to the column-prefix in the source CSV (e.g. 'hdi_1990').
SERIES_PREFIX = {
    "hdi_2025": "hdi",
    "hdi": "hdi",
    "life_expectancy": "le",
    "mean_years_schooling": "mys",
    "expected_years_schooling": "eys",
    "gni_per_capita": "gnipc",
}


def fetch(series_id: str = "hdi_2025", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    if series_id not in SERIES_PREFIX:
        raise ValueError(f"Unknown undp_hdi series_id '{series_id}'; "
                         f"use one of {sorted(SERIES_PREFIX)}")
    prefix = SERIES_PREFIX[series_id]

    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    wide = pd.read_csv(io.BytesIO(r.content), encoding="latin-1")

    # Melt YYYY columns for this prefix.
    year_cols = [c for c in wide.columns
                 if re.fullmatch(rf"{prefix}_\d{{4}}", c)]
    if not year_cols:
        raise RuntimeError(f"No columns matching '{prefix}_YYYY' in HDR 2025 CSV")

    long = wide.melt(
        id_vars=["iso3", "country"],
        value_vars=year_cols,
        var_name="_col",
        value_name="value",
    )
    long["year"] = long["_col"].str.extract(r"(\d{4})").astype("Int64")
    long = long.rename(columns={"iso3": "country_iso3", "country": "country_name"})
    long = long[["country_iso3", "country_name", "year", "value"]]
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    # Drop observations with no value (not all country-year cells are populated)
    long = long.dropna(subset=["value"])

    path_out, sha = write_vintage(
        publisher="undp_hdi",
        series_id=series_id,
        frame=long,
        fetch_utc=fetch_ts,
    )

    start = int(long["year"].min()) if len(long) else None
    end = int(long["year"].max()) if len(long) else None
    units_map = {
        "hdi": "index 0-1",
        "hdi_2025": "index 0-1",
        "life_expectancy": "years",
        "mean_years_schooling": "years",
        "expected_years_schooling": "years",
        "gni_per_capita": "2021 PPP $",
    }
    return FetchResult(
        publisher="undp_hdi",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://hdr.undp.org/data-center",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(long),
        frequency="annual",
        units=units_map.get(series_id, "index"),
        currency=None,
        start_date=str(start) if start else None,
        end_date=str(end) if end else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "prefix": prefix,
            "n_country_year_cells": int(len(long)),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
