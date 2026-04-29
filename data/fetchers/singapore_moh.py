"""Singapore Ministry of Health — manual-drop fetcher.

Source URL (browser):
    https://www.moh.gov.sg/resources-statistics/singapore-health-facts
    https://www.moh.gov.sg/resources-statistics/healthcare-statistics

MOH publishes Singapore Health Facts (annual) with healthcare spending %
GDP, outcome metrics, utilisation, coverage. Essential for refinement
D.2.10 healthcare political-economy comparator.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "health_facts_annual", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("singapore_moh", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        sheet = xls.sheet_names[0]
        df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="singapore_moh", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="singapore_moh", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.moh.gov.sg/resources-statistics",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="mixed (% GDP, per-capita SGD, outcome metrics)",
        currency="SGD", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
