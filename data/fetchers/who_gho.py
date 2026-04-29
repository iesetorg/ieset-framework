"""WHO Global Health Observatory (OData API).

Endpoint: https://ghoapi.azureedge.net/api
Auth: none.
License: CC-BY-NC-SA-3.0 IGO (cite required; non-commercial).
Docs: https://www.who.int/data/gho/info/gho-odata-api

Global health indicators — mortality, DALYs, health expenditure, service
coverage, SDGs. Queried by indicator code (e.g. 'WHOSIS_000001' = life
expectancy at birth).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://ghoapi.azureedge.net/api"
LICENSE = "CC-BY-NC-SA-3.0 IGO"


class WhoError(RuntimeError):
    pass


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: WHO indicator code, e.g., 'WHOSIS_000001' (life expectancy),
    'MDG_0000000001' (IMR), 'SH.DTH.NCOM.ZS' (NCD deaths)."""
    fetch_ts = utc_now()
    r = requests.get(f"{BASE}/{series_id}", timeout=60)
    r.raise_for_status()
    doc = r.json()
    rows = doc.get("value") or []
    if not rows:
        raise WhoError(f"WHO GHO returned no rows for {series_id}")
    df = pd.DataFrame(rows)
    # Standardise common columns
    if "SpatialDim" in df.columns:
        df = df.rename(columns={"SpatialDim": "country_iso3"})
    if "TimeDim" in df.columns:
        df = df.rename(columns={"TimeDim": "year"})
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "NumericValue" in df.columns:
        df["value"] = pd.to_numeric(df["NumericValue"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="who_gho",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="who_gho",
        series_id=series_id,
        source_url=f"{BASE}/{series_id}",
        methodology_url=f"https://www.who.int/data/gho/indicator-metadata-registry/imr-details/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="per indicator",
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
