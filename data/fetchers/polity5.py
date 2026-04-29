"""Polity5 regime authority dataset (Center for Systemic Peace).

Annual country-year ratings of regime authority characteristics from 1800,
with the overall polity score (-10 autocracy to +10 democracy). Parallel axis
to V-Dem for institutional-quality robustness.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://www.systemicpeace.org/inscr/p5v2018.xls"
LICENSE = "academic — Center for Systemic Peace; citation required (Marshall & Gurr 2020)"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


def fetch(series_id: str = "polity5", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    sheet = xls.sheet_names[0]
    df = xls.parse(sheet)
    rename = {c: c.strip().lower() for c in df.columns if isinstance(c, str)}
    df = df.rename(columns=rename)
    if "scode" in df.columns:
        df = df.rename(columns={"scode": "country_iso3_polity"})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    path_out, sha = write_vintage(
        publisher="polity5",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="polity5",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://www.systemicpeace.org/polityproject.html",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="regime score (-10 autocracy to +10 democracy); component scales per codebook",
        currency=None,
        start_date=str(int(df["year"].min())) if "year" in df.columns and len(df) else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "columns_sample": list(df.columns)[:20],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
