"""Statistics Norway (SSB) PXWeb / JSON-stat 2.0 fetcher.

Endpoint:  https://data.ssb.no/api/v0/en/table/<table_id>/
Docs:      https://www.ssb.no/en/api/api-eksempler-pa-bruk
License:   NLOD 2.0 (Norwegian Licence for Open Government Data) — treated as
           cc_by_4_0-equivalent in the publishers registry.

Auth: none.

Series identifier convention: short semantic alias used in spec citations
(e.g. 'GDP', 'formuesskatt_base', 'skatteinntekter', 'utvandring'), each
mapped to a canonical SSB table id and a pre-canned PXWeb query body. Bare
table ids (e.g. '09190') also pass through, in which case we ask for the
table's full content via wildcard selection.

Strategy: POST a small JSON-stat query body to the per-table endpoint with
`response.format = "json-stat2"`, parse the JSON-stat 2.0 payload into a
tidy long DataFrame keyed by (country_iso3='NOR', period, dimensions, value).
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://data.ssb.no/api/v0/en/table"
LICENSE = "cc_by_4_0"  # NLOD 2.0; attribution-style open licence

# Polite-client rate limit: SSB API caps at ~30 requests / 60 s per IP.
_RATE_LIMIT_SECONDS = 0.5
_RATE_LOCK = threading.Lock()
_LAST_CALL_TS = 0.0


# Pre-canned PXWeb query bodies. Each entry maps a series alias to:
#   - table:    SSB table id
#   - title:    human-readable title
#   - frequency, currency, units: metadata for FetchResult
#   - query:    JSON-stat / PXWeb query body (list of dimension selections).
#               Use {"filter": "all", "values": ["*"]} to grab everything for
#               a dimension; "top"/"item" filters narrow it.
SUPPORTED: dict[str, dict[str, Any]] = {
    # GDP — annual main aggregates (table 09190).
    "GDP": {
        "table": "09190",
        "title": "GDP and main national accounts aggregates (annual)",
        "frequency": "annual",
        "currency": "NOK",
        "units": "NOK million / index",
        "query": [
            {"code": "Makrost", "selection": {"filter": "item", "values": ["bnpb.nr23_9"]}},
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # Wealth-tax base — assets and debt by individual (table 04476).
    "formuesskatt_base": {
        "table": "04476",
        "title": "Wealth-tax base — assets and debt of personal taxpayers (annual)",
        "frequency": "annual",
        "currency": "NOK",
        "units": "NOK million",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # General-government tax revenue (table 12404).
    "skatteinntekter": {
        "table": "12404",
        "title": "General government tax revenue (annual)",
        "frequency": "annual",
        "currency": "NOK",
        "units": "NOK million",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
    # Immigration / emigration by citizenship (table 05753).
    "utvandring": {
        "table": "05753",
        "title": "Immigration and emigration by citizenship (annual)",
        "frequency": "annual",
        "currency": None,
        "units": "persons",
        "query": [
            {"code": "ContentsCode", "selection": {"filter": "all", "values": ["*"]}},
            {"code": "Tid", "selection": {"filter": "all", "values": ["*"]}},
        ],
    },
}


class SSBError(RuntimeError):
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
    """Fall-back query for a bare table id: read its metadata to find the
    'Tid' (time) dimension and a content dimension, then ask for everything.

    SSB requires every variable to be selected; an empty body returns 400.
    """
    _rate_limit()
    r = requests.get(f"{BASE}/{table}/", timeout=60)
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
        raise SSBError(f"SSB table {table}: no variables in metadata")
    return selections


def _post_query(table: str, query: list[dict[str, Any]]) -> dict[str, Any]:
    """POST a PXWeb query body and return the JSON-stat 2.0 payload."""
    body = {
        "query": query,
        "response": {"format": "json-stat2"},
    }
    _rate_limit()
    r = requests.post(f"{BASE}/{table}/", json=body, timeout=120)
    if r.status_code >= 400:
        # Surface the API's error text — it's usually a clear 'unknown code'
        # diagnostic for a bad selection.
        raise SSBError(
            f"SSB POST {table} failed [{r.status_code}]: {r.text[:300]}"
        )
    payload = r.json()
    if not isinstance(payload, dict) or "value" not in payload:
        raise SSBError(f"SSB {table}: unexpected payload shape: {str(payload)[:200]}")
    return payload


def _jsonstat_to_long(payload: dict[str, Any]) -> pd.DataFrame:
    """Reshape a JSON-stat 2.0 response into a tidy long DataFrame.

    Closely mirrors the Eurostat reshape in data.fetchers.eurostat.
    """
    dims = payload.get("dimension") or {}
    ids = payload.get("id") or []
    sizes = payload.get("size") or []
    values = payload.get("value")
    if not ids:
        raise SSBError("JSON-stat payload missing 'id'")

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
        raise SSBError(f"JSON-stat 'value' has unexpected type: {type(values).__name__}")

    df = pd.DataFrame(records)
    if df.empty:
        return df
    # SSB convention: 'Tid' is the time dim. Rename to 'period' for consistency.
    if "Tid" in df.columns:
        df = df.rename(columns={"Tid": "period"})
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["country_iso3"] = "NOR"
    return df


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch an SSB table as a tidy long-form DataFrame.

    series_id: a key in SUPPORTED (e.g. 'GDP', 'formuesskatt_base',
               'skatteinntekter', 'utvandring') OR a bare SSB table id
               (e.g. '09190'); unknown ids fall back to a wildcard query
               built from the table's metadata.
    """
    fetch_ts = utc_now()
    meta = SUPPORTED.get(series_id, {})
    table = meta.get("table") or series_id
    query = meta.get("query") or _default_query(table)

    payload = _post_query(table, query)
    df = _jsonstat_to_long(payload)
    if df.empty:
        raise SSBError(f"SSB table {table}: no observations parsed")

    path_out, sha = write_vintage(
        publisher="ssb",
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
        publisher="ssb",
        series_id=series_id,
        source_url=f"{BASE}/{table}/",
        methodology_url=f"https://www.ssb.no/en/statbank/table/{table}",
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
            "country_iso3": "NOR",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
