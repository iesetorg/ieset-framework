"""Saudi General Authority for Statistics (GASTAT) — manual-drop.

Source URL (browser):
    https://www.stats.gov.sa/en/statistics-overview
    https://www.stats.gov.sa/en/national-accounts
    https://www.stats.gov.sa/en/labour-force

National statistics publisher for Saudi GDP, labour force, demographics,
Vision 2030 progress. Direct URLs 404 on automated scraping; browser-UX
gated. Drop files per-topic into data/manual/gastat/.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "gastat_data", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("gastat", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="gastat", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="gastat", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.stats.gov.sa/en",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="quarterly",
        units="per dataset",
        currency="SAR", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
