"""US Bureau of Labor Statistics (BLS) Public API v2.

Endpoint: https://api.bls.gov/publicAPI/v2
Auth: optional (free registration for higher rate limits). Without key: 25
queries/day per IP, 10 series per query, 10 years max. With key: 500 queries/day.

BLS covers US labor at higher resolution than FRED's mirror: CPI detailed,
PPI by industry, employment by state/industry, earnings, productivity.
"""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://api.bls.gov/publicAPI/v2"
LICENSE = "public_domain"


class BlsError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> FetchResult:
    """series_id: BLS series code (e.g., 'CUUR0000SA0' = CPI-U all items)."""
    fetch_ts = utc_now()
    payload: dict = {"seriesid": [series_id]}
    if start_year:
        payload["startyear"] = str(start_year)
    if end_year:
        payload["endyear"] = str(end_year)
    key = os.environ.get("BLS_API_KEY")
    if key:
        payload["registrationkey"] = key
    r = requests.post(
        f"{BASE}/timeseries/data/",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    doc = r.json()
    if doc.get("status") != "REQUEST_SUCCEEDED":
        raise BlsError(f"BLS {series_id} failed: {doc.get('status')} — {doc.get('message')}")
    series_list = doc.get("Results", {}).get("series", [])
    if not series_list:
        raise BlsError(f"BLS {series_id}: no series returned")
    data = series_list[0].get("data", [])
    if not data:
        raise BlsError(f"BLS {series_id}: no observations")
    df = pd.DataFrame(data)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{BASE}/timeseries/data/{series_id}",
        methodology_url=f"https://data.bls.gov/timeseries/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units="per series (index, rate, dollars)",
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) else None,
        end_date=str(int(df["year"].max())) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "bls_registration_key_used": bool(key),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
