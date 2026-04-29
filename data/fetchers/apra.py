"""Australian Prudential Regulation Authority (APRA) — manual-drop.

Source URL (browser):
    https://www.apra.gov.au/annual-fund-level-superannuation-statistics
    https://www.apra.gov.au/quarterly-superannuation-statistics

APRA releases super fund-level + aggregate quarterly statistics xlsx.
Core data for Australian Superannuation forced-saving architecture
(refinement D.1.5 + D.2.9 welfare-architecture comparator).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "cc_by_4_0"  # APRA releases under CC-BY-3.0 AU, treat as CC-BY-4.0 compatible


def fetch(series_id: str = "super_annual", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("apra", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        sheet = next((s for s in xls.sheet_names if any(k in s.lower() for k in ("summary", "data", "aggregate"))), xls.sheet_names[0])
        df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="apra", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="apra", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.apra.gov.au/superannuation-statistics",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="super fund balances AUDbn, member counts, asset allocation %",
        currency="AUD", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
