"""Swiss Health Observatory (OBSAN) — manual-drop fetcher.

Source URL (browser):
    https://www.obsan.admin.ch/en/publications

OBSAN publishes per-topic health monitoring xlsx reports. Drop relevant
files into data/manual/swiss_obsan/ for the Swiss mixed-insurance
healthcare comparator (refinement D.2.10).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "obsan_data", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("swiss_obsan", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="swiss_obsan", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="swiss_obsan", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.obsan.admin.ch/en",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="per dataset",
        units="healthcare monitoring indicators",
        currency="CHF", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
