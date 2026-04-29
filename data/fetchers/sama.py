"""Saudi Arabian Monetary Authority (SAMA) — manual-drop.

Source URL (browser):
    https://www.sama.gov.sa/en-US/EconomicReports/Pages/YearlyStatistics.aspx
    https://www.sama.gov.sa/en-US/EconomicReports/Pages/MonthlyStatistics.aspx

SAMA publishes annual + monthly statistical bulletins as xlsx. Essential
for Saudi macro + SWF-related resource-rent hypothesis work. Direct URLs
404 on all automated attempts; files are public but require browser UX.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "sama_annual", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("sama", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="sama", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="sama", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.sama.gov.sa/en-US/EconomicReports",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="monthly",
        units="SAR-denominated monetary + banking + BOP aggregates",
        currency="SAR", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
