"""World Bank World Development Indicators fetcher.

Auth: none.
Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
License: CC-BY-4.0.

WDI does not expose an explicit vintage API. We snapshot on fetch and rely on
the payload SHA256 + fetch_utc in the manifest to identify the vintage. The
World Bank releases WDI updates roughly quarterly; large re-revisions are
announced on the WDI blog.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

WB_BASE = "https://api.worldbank.org/v2"
LICENSE = "CC-BY-4.0"


class WorldBankError(RuntimeError):
    pass


def _iter_pages(indicator: str, countries: str) -> Iterable[dict]:
    page = 1
    while True:
        # Cross-country pulls on large indicators routinely take >60s; retry
        # transient timeouts with backoff rather than failing the series.
        last_exc: Exception | None = None
        for attempt in (1, 2, 3):
            try:
                r = requests.get(
                    f"{WB_BASE}/country/{countries}/indicator/{indicator}",
                    params={"format": "json", "per_page": 1000, "page": page},
                    timeout=180,
                )
                break
            except requests.ReadTimeout as e:
                last_exc = e
                continue
        else:
            raise WorldBankError(f"WDI timed out 3x fetching {indicator} page={page}: {last_exc}")
        r.raise_for_status()
        payload = r.json()
        if not isinstance(payload, list) or len(payload) < 2:
            # Single-element payload is always an error object from the WB API.
            err = payload[0] if isinstance(payload, list) and payload else payload
            raise WorldBankError(f"WDI error for {indicator}: {err}")
        meta, rows = payload
        if rows is None:
            return
        for row in rows:
            yield row
        if page >= int(meta.get("pages", 1)):
            return
        page += 1


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: str = "all",
) -> FetchResult:
    """Fetch a WDI indicator.

    series_id: WDI indicator code, e.g., NY.GDP.PCAP.KD.
    countries: ISO3 list joined by ';' or 'all' (default).
    """
    fetch_ts = utc_now()
    rows = list(_iter_pages(series_id, countries))
    if not rows:
        raise WorldBankError(f"WDI returned no rows for {series_id}")

    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
    df["country_iso3"] = df["countryiso3code"]
    df["country_name"] = df["country"].apply(lambda c: c.get("value") if isinstance(c, dict) else None)
    df["indicator_id"] = df["indicator"].apply(lambda i: i.get("id") if isinstance(i, dict) else None)
    df = (
        df[["country_iso3", "country_name", "indicator_id", "year", "value", "unit", "obs_status", "decimal"]]
        .dropna(subset=["country_iso3"])
        .sort_values(["country_iso3", "year"])
        .reset_index(drop=True)
    )

    path, sha = write_vintage(
        publisher="world_bank_wdi",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    meta_resp = requests.get(
        f"{WB_BASE}/indicator/{series_id}", params={"format": "json"}, timeout=30
    )
    meta_resp.raise_for_status()
    meta_payload = meta_resp.json()
    meta = meta_payload[1][0] if isinstance(meta_payload, list) and len(meta_payload) > 1 and meta_payload[1] else {}

    return FetchResult(
        publisher="world_bank_wdi",
        series_id=series_id,
        source_url=f"{WB_BASE}/country/{countries}/indicator/{series_id}?format=json",
        methodology_url=f"https://data.worldbank.org/indicator/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=meta.get("unit") or "per indicator definition",
        currency=None,
        start_date=str(df["year"].min()) if len(df) else None,
        end_date=str(df["year"].max()) if len(df) else None,
        sha256=sha,
        parquet_path=path,
        extra={
            "indicator_name": meta.get("name"),
            "source_note": (meta.get("sourceNote") or "")[:400],
            "countries_param": countries,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
