"""World Justice Project Rule of Law Index — manual-drop fetcher.

WJP gates data downloads behind AJAX-loaded UI that both plain requests
and Zenrows (RESP001) cannot reach. Drop the 'Historical Data File' xlsx
into data/manual/wjp_rol/.

Source URL (browser):
    https://worldjusticeproject.org/rule-of-law-index/downloads
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"


def fetch(series_id: str = "historical_panel", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("wjp_rol", "xlsx", "xls")
    fetch_ts = utc_now()
    xls = pd.ExcelFile(path)
    # WJP ships overall score + factor breakdowns per sheet; the first data
    # sheet is usually 'WJP RoL Index <year> scores' or 'All Data'.
    sheet = next(
        (s for s in xls.sheet_names if any(k in s.lower() for k in ("historical", "all data", "data", "scores"))),
        xls.sheet_names[0],
    )
    df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    out, sha = write_vintage(publisher="wjp_rol", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="wjp_rol", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://worldjusticeproject.org/rule-of-law-index/factors/2024",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="Index 0-1 (higher = stronger rule of law); 8 factors + 44 sub-factors",
        currency=None, start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "sheet": sheet, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
