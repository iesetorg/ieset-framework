"""Heritage Foundation Index of Economic Freedom fetcher.

Annual XLSX published at the static subdomain:
    https://static.heritage.org/index/data/<year>/<year>_indexofeconomicfreedom_data.xlsx

The main heritage.org pages block automated access (Cloudflare/Akamai) but
the static subdomain ships files cleanly. curl_cffi with Chrome fingerprint
recommended; plain requests also works on the static subdomain.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from curl_cffi import requests as cffi_requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic_citation"


class HeritageError(RuntimeError):
    pass


def fetch(series_id: str = "ief_2026", *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: e.g. 'ief_2026', 'ief_2024'. Maps to the release-year file."""
    fetch_ts = utc_now()
    year = series_id.split("_")[-1] if "_" in series_id else "2026"
    if not year.isdigit():
        raise HeritageError(f"Cannot parse year from series_id {series_id!r}; use 'ief_YYYY'")
    url = f"https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.xlsx"
    r = cffi_requests.get(url, impersonate="chrome", timeout=60)
    r.raise_for_status()
    if len(r.content) < 1000:
        raise HeritageError(f"Heritage returned small payload: {len(r.content)} bytes (may be HTML error)")

    xls = pd.ExcelFile(io.BytesIO(r.content))
    # Heritage files usually have a single data sheet + legend
    sheet = next(
        (s for s in xls.sheet_names if "data" in s.lower() or s.lower().startswith(("country", "score"))),
        xls.sheet_names[0],
    )
    df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    path_out, sha = write_vintage(
        publisher="heritage_ief",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="heritage_ief",
        series_id=series_id,
        source_url=url,
        methodology_url=f"https://www.heritage.org/index/about",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="Index score 0-100 + component pillars",
        currency=None,
        start_date=str(year),
        end_date=str(year),
        sha256=sha,
        parquet_path=path_out,
        extra={
            "release_year": year,
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "columns": list(df.columns)[:20],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
