"""Uppsala Conflict Data Program (UCDP) Georeferenced Event Dataset.

Conflict events since 1989 with geocoded locations, fatalities, actor
classification. Annual release as a zip of CSV + JSON.
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://ucdp.uu.se/downloads/ged/ged241-csv.zip"
LICENSE = "academic — UCDP; citation required (Sundberg & Melander 2013)"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


class UcdpError(RuntimeError):
    pass


def fetch(series_id: str = "ged_events", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=300)
    r.raise_for_status()
    zbuf = io.BytesIO(r.content)
    with zipfile.ZipFile(zbuf) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise UcdpError(f"no CSV in UCDP zip; contents: {zf.namelist()}")
        # Take the largest CSV (the main events file)
        csv_name = max(csv_names, key=lambda n: zf.getinfo(n).file_size)
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)

    path_out, sha = write_vintage(
        publisher="ucdp",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    year_col = "year" if "year" in df.columns else None
    return FetchResult(
        publisher="ucdp",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://ucdp.uu.se/downloads/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="event",
        units="event-level; fatality counts per event",
        currency=None,
        start_date=str(int(df[year_col].min())) if year_col else None,
        end_date=str(int(df[year_col].max())) if year_col else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "csv_name": csv_name,
            "n_columns": len(df.columns),
            "columns_sample": list(df.columns)[:20],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
