"""Hanke Troubled Currencies — manual-drop fetcher.

Steve Hanke's Troubled Currencies Project publishes monthly parallel-market
inflation estimates for currencies that have broken from official pegs —
essential for post-2012 hyperinflation episodes (Venezuela 2016-2019,
Lebanon 2019-2023, Turkey near-threshold) not covered in the 2012
Hanke-Krus catalogue.

Data is dispersed across Cato Institute pieces and Hanke's Twitter feed;
manual compilation is required. Expected file format: CSV with columns
country_iso3, year, month, monthly_inflation_pct, source, notes.

Source URLs (browser):
    https://sites.krieger.jhu.edu/iae/publications/
    https://www.cato.org/blog?topic=monetary-policy
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"


def fetch(series_id: str = "troubled_currencies_monthly", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("hanke_tc", "csv")
    fetch_ts = utc_now()
    df = pd.read_csv(path)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    out, sha = write_vintage(publisher="hanke_tc", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="hanke_tc", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://sites.krieger.jhu.edu/iae/",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="monthly",
        units="monthly inflation % (parallel-market-implied)",
        currency=None, start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
