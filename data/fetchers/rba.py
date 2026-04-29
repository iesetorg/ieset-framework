"""Reserve Bank of Australia statistical tables fetcher.

RBA Akamai blocks plain requests with 403. curl_cffi with a Chrome TLS
fingerprint slips through cleanly. All RBA statistical-tables XLSX files
live at https://www.rba.gov.au/statistics/tables/xls/<code>hist.xlsx.

Common series:
    d03hist.xlsx   D3 — Monetary Aggregates (M1, M3, Broad Money)
    f01hist.xlsx   F1 — Interest Rates
    g01hist.xlsx   G1 — Consumer Price Inflation
    f11hist.xlsx   F11 — Exchange Rates
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from curl_cffi import requests as cffi_requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www.rba.gov.au/statistics/tables/xls"
LICENSE = "cc_by_4_0"  # RBA statistical tables are CC-BY


class RbaError(RuntimeError):
    pass


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: RBA table code (e.g., 'd03hist', 'f01hist', 'g01hist')."""
    fetch_ts = utc_now()
    url = f"{BASE}/{series_id}.xlsx"
    r = cffi_requests.get(url, impersonate="chrome", timeout=60)
    if r.status_code == 404:
        raise RbaError(f"RBA 404 for {series_id} — check table code; try lower-case + 'hist' suffix")
    r.raise_for_status()
    if len(r.content) < 1000:
        raise RbaError(f"RBA returned suspiciously small payload for {series_id}: {len(r.content)} bytes")

    xls = pd.ExcelFile(io.BytesIO(r.content))
    # RBA tables usually have multiple sheets; pick the 'Data' sheet if present, else first non-'Description'
    sheet = next(
        (s for s in xls.sheet_names if s.lower() == "data"),
        next((s for s in xls.sheet_names if s.lower() != "description" and s.lower() != "notes"), xls.sheet_names[0]),
    )
    # RBA sheets have 10-11 row header preamble; detect where numeric data starts
    raw = xls.parse(sheet, header=None)
    date_col_start = None
    for i in range(min(15, len(raw))):
        # The date column starts where row has a parseable date in col 0
        try:
            pd.to_datetime(raw.iloc[i, 0])
            date_col_start = i
            break
        except (ValueError, TypeError):
            continue
    if date_col_start is None:
        # Fall back to default parse; preserve whatever structure we get
        df = xls.parse(sheet)
    else:
        df = xls.parse(sheet, skiprows=date_col_start - 1)
    # Coerce object columns to string for parquet-safe storage
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    path_out, sha = write_vintage(
        publisher="rba",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="rba",
        series_id=series_id,
        source_url=url,
        methodology_url=f"https://www.rba.gov.au/statistics/tables/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",  # most RBA 'hist' tables are monthly
        units="per table",
        currency="AUD",
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "data_start_row": date_col_start,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
