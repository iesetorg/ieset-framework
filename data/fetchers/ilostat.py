"""ILOSTAT labor statistics.

Endpoint: https://rplumber.ilo.org/data
Auth: none.
License: CC-BY-4.0.

ILO indicators: employment rates, unemployment, wages, hours, informal
employment, labor force participation. Broader country coverage than OECD
(esp. developing countries).

Indicator code format: 'UNE_2EAP_SEX_AGE_RT_A' (Unemployment rate, annual).
Full codes: https://ilostat.ilo.org/resources/methods/description-unemployment/
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://rplumber.ilo.org/data"
LICENSE = "cc_by_4_0"


class IlostatError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    ref_area: str | None = None,
    time_from: str | None = None,
    time_to: str | None = None,
) -> FetchResult:
    """series_id: ILO indicator code.
    ref_area: ISO3 country (or comma-separated list), or None for all.
    time_from / time_to: YYYY bounds."""
    fetch_ts = utc_now()
    params: dict[str, str] = {"id": series_id, "format": ".csv"}
    if ref_area:
        params["ref_area"] = ref_area
    if time_from:
        params["timefrom"] = time_from
    if time_to:
        params["timeto"] = time_to
    r = requests.get(f"{BASE}/indicator/", params=params, timeout=120)
    r.raise_for_status()
    text = r.text
    if not text.strip() or len(text) < 100:
        raise IlostatError(f"ILOSTAT empty response for {series_id}")
    df = pd.read_csv(io.StringIO(text), low_memory=False)
    # Standardise
    if "ref_area" in df.columns:
        df = df.rename(columns={"ref_area": "country_iso3"})
    if "time" in df.columns:
        df["year"] = pd.to_numeric(df["time"], errors="coerce").astype("Int64")
    if "obs_value" in df.columns:
        df["value"] = pd.to_numeric(df["obs_value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="ilostat",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="ilostat",
        series_id=series_id,
        source_url=f"{BASE}/indicator/?id={series_id}&format=.csv",
        methodology_url=f"https://ilostat.ilo.org/data/",
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
            "ref_area": ref_area,
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
