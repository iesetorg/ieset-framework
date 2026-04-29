"""Freedom House — Freedom in the World ratings.

Annual country-year ratings of political rights + civil liberties.
Static xlsx download. Parallel axis to V-Dem + Polity5.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://freedomhouse.org/sites/default/files/2024-02/All_data_FIW_2013-2024.xlsx"
LICENSE = "academic/press — Freedom House; attribution required"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


def fetch(
    series_id: str = "fiw_all_countries",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    # FIW ships multi-sheet — 'FIW13-24' is the aggregate country-year panel.
    sheet = next(
        (s for s in xls.sheet_names if "fiw" in s.lower() or "country" in s.lower()),
        xls.sheet_names[0],
    )
    # Header can be on row 1 or 2 depending on release; detect.
    df = xls.parse(sheet, header=[0, 1]) if any("Year" in str(v) for v in xls.parse(sheet, header=None, nrows=3).iloc[1, :].values) else xls.parse(sheet)
    # Flatten MultiIndex if we got one
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["__".join(str(x) for x in c if str(x) != "nan").strip("_") for c in df.columns]
    rename = {c: c.strip().lower().replace(" ", "_") for c in df.columns if isinstance(c, str)}
    df = df.rename(columns=rename)

    # Freedom House workbook has mixed-type cells in several "unnamed" columns
    # that parquet's Arrow backend rejects. Coerce every object-dtype column to
    # string to make the schema parquet-clean; numeric columns are preserved.
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    path_out, sha = write_vintage(
        publisher="freedom_house",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    year_col = next((c for c in df.columns if "year" in str(c).lower()), None)
    start = str(pd.to_numeric(df[year_col], errors="coerce").min()) if year_col else None
    end = str(pd.to_numeric(df[year_col], errors="coerce").max()) if year_col else None

    return FetchResult(
        publisher="freedom_house",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://freedomhouse.org/reports/publication-archives",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="PR (1-7 best-worst); CL (1-7); Status {F, PF, NF}",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "columns_sample": list(df.columns)[:20],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
