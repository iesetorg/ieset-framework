"""Statistics Sweden (SCB) PxWeb / JSON-stat 2.0 fetcher.

Endpoint:  https://api.scb.se/OV0104/v1/doris/en/ssd/<table_path>
Docs:      https://www.scb.se/en/services/open-data-api/api-for-the-statistical-database/
License:   CC0 (public domain) — SCB releases its statistical database freely.

Auth: none.

Series identifier convention: short semantic alias used in spec citations
(e.g. 'cpi', 'gdp', 'population', 'unemployment'), each mapped to a
canonical SCB table path and a pre-canned PxWeb query body. Bare table
paths (e.g. 'BE/BE0101/BE0101A/BefolkningNy') also pass through, in
which case we ask for the table's full content via wildcard selection
based on the table's metadata.

Strategy: POST a small JSON-stat query body to the per-table endpoint with
`response.format = "json-stat2"`, parse the JSON-stat 2.0 payload into a
tidy long DataFrame keyed by (country_iso3='SWE', period, dimensions, value).

This is structurally identical to data.fetchers.ssb (Norway uses the same
PxWeb protocol); see that module for the longer commentary.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://api.scb.se/OV0104/v1/doris/en/ssd"
LICENSE = "public_domain"  # CC0

# Polite-client rate limit: SCB caps at ~10 calls / 10 s per IP.
_RATE_LIMIT_SECONDS = 1.0
_RATE_LOCK = threading.Lock()
_LAST_CALL_TS = 0.0


# Pre-canned PxWeb query bodies. Each entry maps a series alias to:
#   - table:    SCB table path (slash-delimited)
#   - title:    human-readable title
#   - frequency, currency, units: metadata for FetchResult
#   - query:    JSON-stat / PxWeb query body (list of dimension selections).
#               Use {"filter": "all", "values": ["*"]} to grab everything for
#               a dimension; "top"/"item" filters narrow it.
SUPPORTED: dict[str, dict[str, Any]] = {
    # Population — total and by demographic break, table BefolkningNy.
    "population": {
        "table": "BE/BE0101/BE0101A/BefolkningNy",
        "title": "Population by region, sex, age and year",
        "frequency": "annual",
        "currency": None,
        "units": "persons",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # GDP — annual main aggregates (ENS 2010, table NR0103ENS2010T01A).
    "gdp": {
        "table": "NR/NR0103/NR0103A/NR0103ENS2010T01A",
        "title": "GDP and main national accounts aggregates (annual, ENS2010)",
        "frequency": "annual",
        "currency": "SEK",
        "units": "SEK million / index",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # Consumer Price Index (KPI), monthly, table KPItotM.
    "cpi": {
        "table": "PR/PR0101/PR0101A/KPItotM",
        "title": "Consumer Price Index (KPI), monthly",
        "frequency": "monthly",
        "currency": None,
        "units": "index (1980=100)",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # Unemployment / labour-force survey (AKU), table NAKUBefolkning2Ny.
    "unemployment": {
        "table": "AM/AM0401/AM0401A/NAKUBefolkning2Ny",
        "title": "Labour-force survey (AKU) — population by labour status",
        "frequency": "monthly",
        "currency": None,
        "units": "persons / percent",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
}


class SCBError(RuntimeError):
    pass


def _rate_limit() -> None:
    global _LAST_CALL_TS
    with _RATE_LOCK:
        now = time.monotonic()
        delta = now - _LAST_CALL_TS
        if delta < _RATE_LIMIT_SECONDS:
            time.sleep(_RATE_LIMIT_SECONDS - delta)
        _LAST_CALL_TS = time.monotonic()


def _default_query(table: str) -> list[dict[str, Any]]:
    """Fall-back query for a bare table path: read its metadata to find
    every variable, then ask for everything.

    SCB requires every variable to be selected; an empty body returns 400.
    """
    _rate_limit()
    r = requests.get(f"{BASE}/{table}", timeout=60)
    r.raise_for_status()
    meta = r.json()
    variables = meta.get("variables", []) or []
    selections: list[dict[str, Any]] = []
    for var in variables:
        code = var.get("code")
        if not code:
            continue
        selections.append(
            {"code": code, "selection": {"filter": "all", "values": ["*"]}}
        )
    if not selections:
        raise SCBError(f"SCB table {table}: no variables in metadata")
    return selections


def _post_query(table: str, query: list[dict[str, Any]]) -> dict[str, Any]:
    """POST a PxWeb query body and return the JSON-stat 2.0 payload."""
    body = {
        "query": query,
        "response": {"format": "json-stat2"},
    }
    _rate_limit()
    r = requests.post(f"{BASE}/{table}", json=body, timeout=120)
    if r.status_code >= 400:
        # Surface the API's error text — usually a clear 'unknown code'
        # diagnostic for a bad selection.
        raise SCBError(
            f"SCB POST {table} failed [{r.status_code}]: {r.text[:300]}"
        )
    payload = r.json()
    if not isinstance(payload, dict) or "value" not in payload:
        raise SCBError(f"SCB {table}: unexpected payload shape: {str(payload)[:200]}")
    return payload


def _jsonstat_to_long(payload: dict[str, Any]) -> pd.DataFrame:
    """Reshape a JSON-stat 2.0 response into a tidy long DataFrame."""
    dims = payload.get("dimension") or {}
    ids = payload.get("id") or []
    sizes = payload.get("size") or []
    values = payload.get("value")
    if not ids:
        raise SCBError("JSON-stat payload missing 'id'")

    # Per-dimension ordered list of category codes.
    dim_codes: dict[str, list[str]] = {}
    dim_labels: dict[str, dict[str, str]] = {}
    for d in ids:
        cat = (dims.get(d) or {}).get("category") or {}
        index = cat.get("index") or {}
        label = cat.get("label") or {}
        if isinstance(index, dict):
            ordered = [k for k, _ in sorted(index.items(), key=lambda kv: kv[1])]
        else:
            ordered = list(index)
        dim_codes[d] = ordered
        dim_labels[d] = label

    # Row-major strides so flat index -> per-dim coordinates.
    strides: list[int] = []
    s = 1
    for sz in reversed(sizes):
        strides.insert(0, s)
        s *= sz
    total = s

    def _coords_for(idx: int) -> dict[str, str]:
        remainder = idx
        coords: dict[str, str] = {}
        for i, dim in enumerate(ids):
            pos = remainder // strides[i]
            remainder = remainder % strides[i]
            if pos < len(dim_codes[dim]):
                coords[dim] = dim_codes[dim][pos]
        return coords

    records: list[dict[str, Any]] = []
    if isinstance(values, dict):
        # Sparse map: {flat_index: value}
        for k, v in values.items():
            try:
                idx = int(k)
            except (TypeError, ValueError):
                continue
            if idx >= total:
                continue
            row = _coords_for(idx)
            row["value"] = v
            records.append(row)
    elif isinstance(values, list):
        # Dense flat array.
        for idx, v in enumerate(values):
            if v is None:
                continue
            row = _coords_for(idx)
            row["value"] = v
            records.append(row)
    else:
        raise SCBError(f"JSON-stat 'value' has unexpected type: {type(values).__name__}")

    df = pd.DataFrame(records)
    if df.empty:
        return df
    # SCB convention: 'Tid' is the time dim. Rename to 'period' for consistency.
    if "Tid" in df.columns:
        df = df.rename(columns={"Tid": "period"})
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["country_iso3"] = "SWE"
    return df


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch an SCB table as a tidy long-form DataFrame.

    series_id: a key in SUPPORTED (e.g. 'cpi', 'gdp', 'population',
               'unemployment') OR a bare SCB table path
               (e.g. 'BE/BE0101/BE0101A/BefolkningNy'); unknown ids fall
               back to a wildcard query built from the table's metadata.
    """
    fetch_ts = utc_now()
    meta = SUPPORTED.get(series_id, {})
    table = meta.get("table") or series_id
    query = meta.get("query") or _default_query(table)

    payload = _post_query(table, query)
    df = _jsonstat_to_long(payload)
    if df.empty:
        raise SCBError(f"SCB table {table}: no observations parsed")

    path_out, sha = write_vintage(
        publisher="scb",
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

    # Methodology link: SCB's English statistical-database table viewer.
    methodology_url = (
        f"https://www.statistikdatabasen.scb.se/pxweb/en/ssd/START__{table.replace('/', '__')}/"
    )

    return FetchResult(
        publisher="scb",
        series_id=series_id,
        source_url=f"{BASE}/{table}",
        methodology_url=methodology_url,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency", "annual"),
        units=meta.get("units", "per table metadata"),
        currency=meta.get("currency"),
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "table": table,
            "title": meta.get("title", payload.get("label", "")[:200]),
            "updated": payload.get("updated"),
            "columns": list(df.columns),
            "country_iso3": "SWE",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
