"""UK Office for National Statistics (ONS) fetcher.

Endpoint (workhorse): https://www.ons.gov.uk/<topic>/timeseries/<series_id>/<dataset>/data
Auth: none. License: UK Open Government Licence v3.0.

The ONS Beta API at api.beta.ons.gov.uk exposes catalogue/metadata, but every
public timeseries CDID resolves to a JSON document at the legacy URL above
which carries the full vintage in `years` / `quarters` / `months` arrays plus
a `description` block with units, title, etc.

Series resolution requires both a CDID (e.g. 'ABMI' for chained-volume GDP)
and a dataset code (e.g. 'UKEA' for the UK Economic Accounts). We register
the IESET-relevant pairs in `SUPPORTED` and resolve at fetch time.

The 'topic' segment in the URL is purely cosmetic — ONS accepts requests at
'/economy/<anything>/timeseries/<id>/<dataset>/data' and also responds at
the bare '/timeseries/<id>/<dataset>/data' shortcut, which we use to avoid
hard-coding topic paths per series.
"""
from __future__ import annotations

import time
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www.ons.gov.uk"
LICENSE = "ogl_uk_3_0"
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Accept": "application/json",
}

# Throttle between requests when fetch() is called in a loop by callers.
_REQUEST_SLEEP_S = 0.2


class OnsError(RuntimeError):
    pass


# Map of CDID -> (topic, dataset). The full URL is
# `https://www.ons.gov.uk/<topic>/timeseries/<cdid>/<dataset>/data`. ONS
# deprecated the bare /timeseries/<cdid>/<dataset>/data shortcut in 2024 —
# the topic prefix is now required. The dataset codes are lowercase.
SUPPORTED: dict[str, tuple[str, str]] = {
    # GDP, chained volume measure, quarterly — Quarterly National Accounts
    "ABMI": ("economy/grossdomesticproductgdp", "qna"),
    # CPI all-items index, monthly — Consumer Prices Inflation
    "D7BT": ("economy/inflationandpriceindices", "mm23"),
    # ILO unemployment rate (16+, all persons), monthly — Labour Market Statistics
    "MGSX": ("employmentandlabourmarket/peoplenotinwork/unemployment", "lms"),
    # Real average weekly earnings, total pay, monthly — EARN01
    "KAB9": ("employmentandlabourmarket/peopleinwork/earningsandworkinghours", "emp"),
    # CPI all-items index (alt CDID), monthly
    "CHAW": ("economy/inflationandpriceindices", "mm23"),
    # Real GDP per head, quarterly — Quarterly National Accounts
    "IHXW": ("economy/grossdomesticproductgdp", "qna"),
    # CPIH all-items index, monthly — Consumer Prices Inflation
    "L55O": ("economy/inflationandpriceindices", "mm23"),
    # Productivity (output per hour, whole economy), quarterly — PRDY
    "LZVB": ("employmentandlabourmarket/peopleinwork/labourproductivity", "prdy"),
    # CPI 12-month inflation rate, monthly
    "D7G7": ("economy/inflationandpriceindices", "mm23"),
    # Real GDP, chained volume, annual — UK Economic Accounts
    "ABMM": ("economy/grossdomesticproductgdp", "ukea"),
    # Average weekly earnings, regular pay, monthly
    "KAI7": ("employmentandlabourmarket/peopleinwork/earningsandworkinghours", "emp"),
    # Employment rate (16-64), monthly LFS
    "LF24": ("employmentandlabourmarket/peopleinwork/employmentandemployeetypes", "lms"),
    # Total economy productivity (output per worker), quarterly
    "A4YM": ("employmentandlabourmarket/peopleinwork/labourproductivity", "prdy"),
    # House price index — UK all-property monthly (alt — uses housingpriceindex topic)
    "CDKO": ("economy/inflationandpriceindices", "hpi"),
}


def _coerce_period(row: dict) -> str | None:
    """Return ONS period string. ONS already gives ISO-ish dates in 'date'.

    Examples observed in the wild:
      - annual:    {"date": "1955", "year": "1955"}
      - quarterly: {"date": "1955 Q1", "year": "1955", "quarter": "Q1"}
      - monthly:   {"date": "1988 JAN", "year": "1988", "month": "January"}
    """
    val = row.get("date")
    if val:
        return str(val).strip()
    # Fallbacks
    y = row.get("year")
    q = row.get("quarter")
    m = row.get("month")
    if y and q:
        return f"{y} {q}"
    if y and m:
        return f"{y} {str(m)[:3].upper()}"
    if y:
        return str(y)
    return None


def _payload_to_long(payload: dict, series_id: str) -> pd.DataFrame:
    records: list[dict] = []
    for bucket, freq in (("years", "annual"), ("quarters", "quarterly"), ("months", "monthly")):
        rows = payload.get(bucket) or []
        for row in rows:
            period = _coerce_period(row)
            v = row.get("value")
            try:
                value = float(v) if v not in (None, "", ".") else None
            except (TypeError, ValueError):
                value = None
            records.append(
                {
                    "date": period,
                    "value": value,
                    "frequency": freq,
                    "country": "GBR",
                    "series_id": series_id,
                }
            )
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.dropna(subset=["date"]).reset_index(drop=True)
    return df


def _infer_frequency(df: pd.DataFrame) -> str:
    if df.empty or "frequency" not in df.columns:
        return "unknown"
    freqs = df["frequency"].dropna().unique().tolist()
    if len(freqs) == 1:
        return freqs[0]
    # ONS payloads frequently include both monthly and annual rollups for the
    # same CDID; report the highest-frequency bucket present.
    for cand in ("monthly", "quarterly", "annual"):
        if cand in freqs:
            return cand
    return "mixed"


def _resolve(series_id: str, dataset: str | None) -> tuple[str, str]:
    """Return (topic, dataset) tuple. SUPPORTED maps CDID -> (topic, dataset);
    callers can override the dataset via kwarg (the topic still comes from the
    registry — pass an unregistered CDID and supply dataset to use the
    'economy' topic catch-all)."""
    sid = series_id.upper()
    if sid in SUPPORTED:
        topic, default_ds = SUPPORTED[sid]
        return topic, dataset or default_ds
    if dataset:
        return "economy", dataset
    raise OnsError(
        f"ONS series '{series_id}' not in SUPPORTED registry; "
        f"pass dataset='<DATASET>' explicitly or extend data/fetchers/ons.py."
    )


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    dataset: str | None = None,
) -> FetchResult:
    """Fetch a single ONS timeseries by CDID.

    series_id: ONS CDID (e.g. 'ABMI', 'D7BT'). Case-insensitive.
    dataset:   ONS dataset code (e.g. 'qna', 'mm23'). Optional if the CDID
               is registered in SUPPORTED.
    """
    sid = series_id.strip().upper()
    topic, ds = _resolve(sid, dataset)
    fetch_ts = utc_now()

    url = f"{BASE}/{topic}/timeseries/{sid.lower()}/{ds.lower()}/data"
    r = requests.get(url, headers=UA, timeout=60)
    time.sleep(_REQUEST_SLEEP_S)
    if r.status_code == 404:
        raise OnsError(f"ONS 404 for series='{sid}' dataset='{ds}' — check CDID/dataset pair")
    r.raise_for_status()
    try:
        payload = r.json()
    except ValueError as e:
        raise OnsError(f"ONS {sid}/{ds}: response was not JSON ({e})")

    df = _payload_to_long(payload, sid)
    if df.empty:
        raise OnsError(f"ONS {sid}/{ds} returned no observations")

    path_out, sha = write_vintage(
        publisher="ons",
        series_id=sid,
        frame=df,
        fetch_utc=fetch_ts,
    )

    desc = payload.get("description") or {}
    title = desc.get("title") or sid
    units = desc.get("unit") or "per series metadata"

    periods = df["date"].dropna().astype(str)
    start = periods.min() if not periods.empty else None
    end = periods.max() if not periods.empty else None

    return FetchResult(
        publisher="ons",
        series_id=sid,
        source_url=url,
        methodology_url=f"{BASE}/timeseries/{sid.lower()}/{ds.lower()}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_infer_frequency(df),
        units=units,
        currency="GBP",
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "dataset": ds,
            "title": title[:200] if isinstance(title, str) else None,
            "release_date": desc.get("releaseDate"),
            "next_release": desc.get("nextRelease"),
            "preunit": desc.get("preUnit"),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
