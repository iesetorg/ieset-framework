"""Bank of Japan — manual-drop fetcher.

Source URL (browser):
    https://www.stat-search.boj.or.jp/ → select series → CSV download

BoJ's stat-search portal is form-driven with session state; automated
scrape of the data tables fails. Users download per-series CSVs and drop
into data/manual/boj/.

Canonical series for IESET:
    money-stock-m2.csv   — MA'MS1M (Money Stock, M2, monthly)
    base-money.csv       — MA'MS2M (Monetary Base, monthly)
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "money_stock_m2", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("boj", "csv", "xlsx", "xls")
    fetch_ts = utc_now()
    if path.suffix.lower() in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    else:
        df = pd.read_csv(path)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="boj", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="boj", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.boj.or.jp/en/statistics/outline/index.htm",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="monthly",
        units="JPY-denominated (money aggregates, rates)",
        currency="JPY", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
