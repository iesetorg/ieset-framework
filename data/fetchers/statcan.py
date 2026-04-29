"""Statistics Canada Web Data Service (WDS) REST fetcher.

Endpoint: https://www150.statcan.gc.ca/t1/wds/rest
Auth: none. License: Statistics Canada Open Licence.
Docs: https://www.statcan.gc.ca/en/developers/wds

Series identified by StatCan 'vectorId' (numeric), e.g. 41552796 for
'Canada; M2 (gross)'. WDS returns JSON.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www150.statcan.gc.ca/t1/wds/rest"
LICENSE = "statcan_open"


class StatCanError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    latest_n: int = 1200,
) -> FetchResult:
    """series_id: StatCan vectorId as a string (we coerce to int).
    latest_n: number of most recent periods to request (max ~1200)."""
    try:
        vector_id = int(series_id.lstrip("v"))
    except ValueError as e:
        raise StatCanError(f"series_id must be numeric vectorId; got {series_id!r}") from e

    fetch_ts = utc_now()
    r = requests.post(
        f"{BASE}/getDataFromVectorsAndLatestNPeriods",
        json=[{"vectorId": vector_id, "latestN": latest_n}],
        timeout=60,
    )
    r.raise_for_status()
    payload = r.json()
    if not isinstance(payload, list) or not payload:
        raise StatCanError(f"StatCan returned unexpected payload: {payload!r}")
    entry = payload[0]
    if entry.get("status") != "SUCCESS":
        raise StatCanError(f"StatCan failure for v{vector_id}: {entry}")
    obj = entry.get("object") or {}
    observations = obj.get("vectorDataPoint") or []
    if not observations:
        raise StatCanError(f"StatCan v{vector_id}: empty vectorDataPoint")

    df = pd.DataFrame(observations)
    if "refPer" in df.columns:
        df = df.rename(columns={"refPer": "period"})
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="statcan",
        series_id=f"v{vector_id}",
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="statcan",
        series_id=f"v{vector_id}",
        source_url=f"{BASE}/getDataFromVectorsAndLatestNPeriods (vectorId={vector_id})",
        methodology_url=f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={obj.get('productId','')}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_freq_code_to_label(obj.get("frequencyCode")),
        units="per table",
        currency="CAD",
        start_date=str(df["period"].min()) if "period" in df.columns and len(df) else None,
        end_date=str(df["period"].max()) if "period" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "title_en": obj.get("SeriesTitleEn", "")[:200],
            "product_id": obj.get("productId"),
            "frequency_code": obj.get("frequencyCode"),
            "scalar_factor_code": obj.get("scalarFactorCode"),
            "latest_n": latest_n,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _freq_code_to_label(code: int | None) -> str:
    return {
        1: "annual", 2: "semi_annual", 4: "quarterly", 6: "monthly",
        7: "biweekly", 8: "weekly", 9: "daily",
    }.get(code, "unknown")
