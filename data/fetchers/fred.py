"""FRED / ALFRED fetcher.

Auth: free API key via FRED_API_KEY env var
      (register at https://fredaccount.stlouisfed.org/apikey).
Docs: https://fred.stlouisfed.org/docs/api/fred/
License: mostly US public domain; some third-party rebundled series carry
attribution requirements (reported in series metadata).
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

FRED_BASE = "https://api.stlouisfed.org/fred"
LICENSE = "mixed (US federal public domain for most series; per-series attribution otherwise)"


class FredError(RuntimeError):
    pass


def _redact_api_key(text: object) -> str:
    return re.sub(r"api_key=[^&\\s)]+", "api_key=<redacted>", str(text))


def _api_key() -> str:
    k = os.environ.get("FRED_API_KEY")
    if not k:
        raise FredError(
            "FRED_API_KEY not set. Register free at "
            "https://fredaccount.stlouisfed.org/apikey and export FRED_API_KEY."
        )
    return k


def _request(path: str, params: dict[str, Any]) -> dict:
    params = {**params, "api_key": _api_key(), "file_type": "json"}
    last: Exception | None = None
    for attempt in (1, 2, 3):
        try:
            r = requests.get(f"{FRED_BASE}/{path}", params=params, timeout=30)
        except requests.RequestException as e:
            last = FredError(_redact_api_key(e))
            time.sleep(2**attempt)
            continue
        if r.status_code == 429 or 500 <= r.status_code < 600:
            time.sleep(2**attempt)
            continue
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise FredError(_redact_api_key(e)) from None
        return r.json()
    raise FredError(f"FRED {path} retries exhausted: {last}")


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """Fetch a FRED series.

    vintage_utc=None pulls the current vintage (latest release). A non-None
    vintage_utc uses ALFRED realtime_start/end to pull the vintage as known at
    that UTC date.
    """
    fetch_ts = utc_now()
    meta_payload = _request("series", {"series_id": series_id})
    seriess = meta_payload.get("seriess") or []
    if not seriess:
        raise FredError(f"FRED returned no metadata for {series_id}")
    meta = seriess[0]

    obs_params: dict[str, Any] = {"series_id": series_id}
    if vintage_utc is not None:
        d = vintage_utc.date().isoformat()
        obs_params["realtime_start"] = d
        obs_params["realtime_end"] = d
    obs = _request("series/observations", obs_params).get("observations") or []
    if not obs:
        raise FredError(f"FRED returned no observations for {series_id}")

    df = pd.DataFrame(obs)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "value", "realtime_start", "realtime_end"]].sort_values("date").reset_index(drop=True)

    path, sha = write_vintage(
        publisher="fred",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="fred",
        series_id=series_id,
        source_url=f"{FRED_BASE}/series/observations?series_id={series_id}",
        methodology_url=f"https://fred.stlouisfed.org/series/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency_short", "unknown"),
        units=meta.get("units", "unknown"),
        currency=None,
        start_date=df["date"].min().date().isoformat(),
        end_date=df["date"].max().date().isoformat(),
        sha256=sha,
        parquet_path=path,
        extra={
            "title": meta.get("title"),
            "seasonal_adjustment": meta.get("seasonal_adjustment_short"),
            "last_updated": meta.get("last_updated"),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
