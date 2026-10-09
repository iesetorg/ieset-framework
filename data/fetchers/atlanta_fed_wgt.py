"""Federal Reserve Bank of Atlanta — Wage Growth Tracker (CPS-based).

File: https://www.atlantafed.org/-/media/Project/Atlanta/FRBA/Documents/datafiles/chcs/wage-growth-tracker/wage-growth-data.xlsx
(old /-/media/documents/... path now 404s — moved in the 2026 site rebuild.)
Auth: none.  License: free use with attribution to FRB Atlanta.

Median 12-month growth in individual hourly wages, 3-month moving average.
series_id: workbook sheet, e.g. "data_overall" (default), "Average Wage Quartile",
"Job Switcher", "Industry", "Paid Hourly". First column is the month.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import BROWSER_UA, save_raw

URL = ("https://www.atlantafed.org/-/media/Project/Atlanta/FRBA/Documents/datafiles/"
       "chcs/wage-growth-tracker/wage-growth-data.xlsx")
LICENSE = "Federal Reserve Bank of Atlanta (attribution required)"


def fetch(series_id: str = "data_overall", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers={"User-Agent": BROWSER_UA}, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b"PK"):
        raise RuntimeError("Atlanta Fed WGT: response is not an xlsx (URL moved?)")
    save_raw("atlanta_fed_wgt", "wage-growth-data", r.content, fetch_ts, "xlsx")
    sheet = pd.read_excel(io.BytesIO(r.content), sheet_name=series_id, header=None)
    hdr = next(i for i in range(10) if sheet.iloc[i, 1:].notna().sum() >= 1 and pd.isna(sheet.iloc[i, 0]))
    cols = ["date"] + [str(c).strip() for c in sheet.iloc[hdr, 1:]]
    body = sheet.iloc[hdr + 1:].copy()
    body.columns = cols
    body = body[pd.to_datetime(body["date"], errors="coerce").notna()]
    body["date"] = pd.to_datetime(body["date"])
    long = body.melt(id_vars="date", var_name="group", value_name="median_wage_growth_pct")
    long["median_wage_growth_pct"] = pd.to_numeric(long["median_wage_growth_pct"], errors="coerce")
    long = long.dropna().reset_index(drop=True)
    name = f"wgt_{series_id}"
    path, sha = write_vintage(publisher="atlanta_fed_wgt", series_id=name, frame=long, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="atlanta_fed_wgt", series_id=name, source_url=URL,
        methodology_url="https://www.atlantafed.org/research-and-data/data/wage-growth-tracker",
        license=LICENSE, fetch_utc=fetch_ts, rows=len(long), frequency="monthly",
        units="percent, 12-month median hourly wage growth, 3mma", currency=None,
        start_date=str(long["date"].min().date()), end_date=str(long["date"].max().date()),
        sha256=sha, parquet_path=path,
        extra={"groups": sorted(long["group"].unique().tolist())[:40],
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
