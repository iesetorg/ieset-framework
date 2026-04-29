"""Eurostat (EU statistical office) fetcher.

Endpoint: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data
Auth: none. License: CC-BY-4.0.

Format: JSON-stat 2.0. Each dataset has a code (e.g. 'nama_10_gdp' for GDP
main aggregates, 'prc_hicp_manr' for HICP yoy, 'une_rt_a' for unemployment).

JSON-stat returns dimensional data; we reshape to tidy long form.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
LICENSE = "cc_by_4_0"


class EurostatError(RuntimeError):
    pass


def _jsonstat_to_long(payload: dict) -> pd.DataFrame:
    """Reshape a JSON-stat 2.0 response to a tidy long DataFrame."""
    dims = payload.get("dimension") or {}
    ids = payload.get("id") or []
    sizes = payload.get("size") or []
    values = payload.get("value") or {}
    if not ids:
        raise EurostatError("JSON-stat payload missing 'id'")

    # For each dimension build ordered list of category codes + labels.
    dim_codes: dict[str, list[str]] = {}
    dim_labels: dict[str, dict[str, str]] = {}
    for d in ids:
        cat = (dims.get(d) or {}).get("category") or {}
        index = cat.get("index") or {}
        label = cat.get("label") or {}
        # index can be dict {code: position} or list [code1, code2, ...]
        if isinstance(index, dict):
            ordered = [k for k, _ in sorted(index.items(), key=lambda kv: kv[1])]
        else:
            ordered = list(index)
        dim_codes[d] = ordered
        dim_labels[d] = label

    # Value index -> multi-dim coordinates via size array (row-major)
    strides = []
    s = 1
    for sz in reversed(sizes):
        strides.insert(0, s)
        s *= sz
    total = s

    records = []
    # value map is sparse-dict in JSON-stat 2 (keys are string indices into the flat array)
    for k, v in values.items():
        idx = int(k)
        if idx >= total:
            continue
        remainder = idx
        coords: dict[str, str] = {}
        for i, dim in enumerate(ids):
            pos = remainder // strides[i]
            remainder = remainder % strides[i]
            if pos < len(dim_codes[dim]):
                coords[dim] = dim_codes[dim][pos]
        coords["value"] = v
        records.append(coords)

    df = pd.DataFrame(records)
    # Promote standard columns
    if "geo" in df.columns:
        df = df.rename(columns={"geo": "geo_code"})
    if "time" in df.columns:
        df = df.rename(columns={"time": "period"})
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    params: dict | None = None,
) -> FetchResult:
    """series_id: Eurostat dataset code, e.g. 'nama_10_gdp', 'une_rt_a'.
    params: optional dict of filter parameters (e.g. {'geo': 'DE', 'time': '2023'}).
    """
    fetch_ts = utc_now()
    q = {"format": "JSON"}
    if params:
        q.update(params)
    r = requests.get(f"{BASE}/{series_id}", params=q, timeout=120)
    r.raise_for_status()
    payload = r.json()
    if "error" in payload:
        raise EurostatError(f"Eurostat error for {series_id}: {payload.get('error')}")
    df = _jsonstat_to_long(payload)
    if df.empty:
        raise EurostatError(f"Eurostat {series_id} returned no observations")

    path_out, sha = write_vintage(
        publisher="eurostat",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "period" in df.columns:
        periods = df["period"].dropna().astype(str)
        if not periods.empty:
            start = periods.min()
            end = periods.max()

    return FetchResult(
        publisher="eurostat",
        series_id=series_id,
        source_url=f"{BASE}/{series_id}?format=JSON",
        methodology_url=f"https://ec.europa.eu/eurostat/databrowser/view/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_infer_frequency(df),
        units="per dataset metadata",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "label": (payload.get("label") or "")[:200],
            "updated": payload.get("updated"),
            "filter_params": params or {},
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _infer_frequency(df: pd.DataFrame) -> str:
    if "freq" in df.columns:
        freqs = df["freq"].dropna().unique().tolist()
        if len(freqs) == 1:
            return {"A": "annual", "Q": "quarterly", "M": "monthly", "D": "daily"}.get(freqs[0], str(freqs[0]))
    if "period" in df.columns:
        sample = df["period"].dropna().astype(str).head(5).tolist()
        if sample:
            s = sample[0]
            if "Q" in s:
                return "quarterly"
            if "M" in s or (len(s) == 7 and s[4] == "-"):
                return "monthly"
            if len(s) == 4 and s.isdigit():
                return "annual"
    return "unknown"
