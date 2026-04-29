"""Maddison Project Database (long-run real GDP).

Source: Groningen Growth and Development Centre. Single xlsx, static URL,
annual refresh cadence (last release mpd2020).

Bolt & van Zanden (2020). Covers GDP per capita in 2011 int'l $ from year 1
for select economies, expanding to broad coverage post-1500.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://www.rug.nl/ggdc/historicaldevelopment/maddison/data/mpd2020.xlsx"
LICENSE = "academic — GGDC Maddison Project; citation required (Bolt & van Zanden 2020)"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


def fetch(series_id: str = "mpd2020", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    # Full country-year panel lives on the 'Full data' sheet in mpd2020.
    sheet = next((s for s in xls.sheet_names if "full" in s.lower() or "data" in s.lower()), xls.sheet_names[0])
    df = xls.parse(sheet)
    # Standardise columns
    rename = {c: c.strip().lower() for c in df.columns if isinstance(c, str)}
    df = df.rename(columns=rename)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "countrycode" in df.columns:
        df = df.rename(columns={"countrycode": "country_iso3"})
    elif "iso" in df.columns:
        df = df.rename(columns={"iso": "country_iso3"})

    path_out, sha = write_vintage(
        publisher="maddison",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="maddison",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://www.rug.nl/ggdc/historicaldevelopment/maddison/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="real GDP per capita (2011 int'l $); population (000s)",
        currency="int_usd_2011",
        start_date=str(int(df["year"].min())) if "year" in df.columns and len(df) else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sheet_used": sheet,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
