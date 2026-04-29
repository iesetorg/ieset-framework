"""Transparency International Corruption Perceptions Index — manual-drop.

Source URL (browser):
    https://www.transparency.org/en/cpi/2024 → Download button

TI's CDN returns 403 to all automated-access vectors tried (plain, curl_cffi,
Zenrows). OWID mirror is still available for a time-series slice
(publisher=owid, series=ti-corruption-perception-index). The manual
fetcher here is the authoritative source with full sub-indicators.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "cc_by_4_0"


def fetch(series_id: str = "cpi_annual", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("transparency_cpi", "xlsx", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        sheet = next((s for s in xls.sheet_names if any(k in s.lower() for k in ("cpi", "result", "score", "data"))), xls.sheet_names[0])
        df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    out, sha = write_vintage(publisher="transparency_cpi", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="transparency_cpi", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.transparency.org/en/cpi/methodology",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="CPI score 0-100 (higher = less corrupt) + ranks",
        currency=None, start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
