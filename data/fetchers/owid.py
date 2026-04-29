"""Our World in Data (OWID) grapher-CSV fetcher.

Endpoint: https://ourworldindata.org/grapher/<slug>.csv
Auth: none. License: CC-BY-4.0 (chart data); attribution flows to original
publisher for each metric.

OWID is the practical bridge for series whose primary publisher has poor
machine access — Transparency CPI, World Happiness Report, Gallup World
Poll-derived trust, WVS-derived indicators, etc. Every grapher chart on
ourworldindata.org exposes `<slug>.csv` for download.

series_id is the grapher slug (e.g., 'ti-corruption-perception-index',
'happiness-cantril-ladder'). Use CC-BY-4.0 + cite the original source
listed in the CSV.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://ourworldindata.org/grapher"
LICENSE = "cc_by_4_0"


class OwidError(RuntimeError):
    pass


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id is the grapher slug."""
    fetch_ts = utc_now()
    url = f"{BASE}/{series_id}.csv"
    r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0 IESET"})
    r.raise_for_status()
    if "csv" not in (r.headers.get("content-type") or "").lower():
        raise OwidError(f"OWID {series_id}: unexpected content-type {r.headers.get('content-type')}")
    df = pd.read_csv(io.StringIO(r.text))
    # OWID CSVs have consistent columns: Entity, Code, Year, <metric columns...>
    if "Code" in df.columns:
        df = df.rename(columns={"Code": "country_iso3", "Entity": "country_name", "Year": "year"})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    path_out, sha = write_vintage(
        publisher="owid",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="owid",
        series_id=series_id,
        source_url=url,
        methodology_url=f"https://ourworldindata.org/grapher/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",  # most OWID series are annual; a few aren't
        units="per chart (see OWID page for units)",
        currency=None,
        start_date=str(int(df["year"].min())) if "year" in df.columns and df["year"].notna().any() else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns and df["year"].notna().any() else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
