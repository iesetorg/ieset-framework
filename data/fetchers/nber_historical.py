"""NBER Historical Macrohistory Database (pre-1929 US macro).

Source: NBER Macrohistory Database — series compiled by NBER from primary
historical statistics (Lebergott unemployment, Persons/Frickey industrial
production, Friedman-Schwartz money stock, pig-iron production, freight
carloadings, etc.). Index page:
    https://www.nber.org/research/data/nber-macrohistory-database
File index:
    https://data.nber.org/databases/macrohistory/contents/

Strategy: many NBER macrohistory series are mirrored at FRED with stable
``M*NNBR`` series IDs and FRED is already a registered fetcher with vintage-
aware ALFRED support. For each supported series we therefore *prefer* the FRED
mirror (by delegating to ``data.fetchers.fred.fetch``) and fall back to a
direct CSV download from ``data.nber.org`` for series that have no FRED mirror.

License: public domain (NBER macrohistory was assembled from US public-domain
statistical sources; NBER itself releases the database without restriction).
"""
from __future__ import annotations

import io
from dataclasses import replace
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from . import fred as fred_fetcher
from ._base import FetchResult, utc_now, write_vintage

PUBLISHER = "nber_historical"
LICENSE = "public_domain"
METHODOLOGY_URL = "https://www.nber.org/research/data/nber-macrohistory-database"
NBER_CONTENTS = "https://data.nber.org/databases/macrohistory/contents/"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


# id -> spec dict.
#   fred_id     : if present, prefer FRED mirror.
#   nber_csv    : direct CSV at data.nber.org/databases/macrohistory/rectdata/...
#   description : short human-readable label.
#   units, frequency : metadata defaults if not derivable.
SUPPORTED: dict[str, dict[str, Any]] = {
    "nber_us_industrial_production_1880_1939": {
        "fred_id": "M1204AUSM363NNBR",
        "description": "US industrial production, Persons/NBER, 1880-1939 (monthly index)",
        "units": "index",
        "frequency": "monthly",
    },
    "nber_us_unemployment_lebergott_1890_1990": {
        "fred_id": "M0892AUSM156NNBR",
        "description": "US unemployment rate, Lebergott / NBER series, 1890-1990",
        "units": "percent of labor force",
        "frequency": "monthly",
    },
    "nber_us_m1_money_stock_1867_1960": {
        "fred_id": "M14062USM027NNBR",
        "description": "US M1 money stock, Friedman-Schwartz / NBER, 1867-1960",
        "units": "billions of USD",
        "frequency": "monthly",
    },
    "nber_us_pig_iron_production_1854_1948": {
        "fred_id": "M01156USM316NNBR",
        "description": "US pig-iron production, NBER, 1854-1948",
        "units": "thousands of long tons",
        "frequency": "monthly",
    },
    "nber_us_freight_carloadings_1918_1947": {
        # No stable FRED mirror; use NBER direct CSV.
        "nber_csv": "https://data.nber.org/databases/macrohistory/rectdata/03/m03048a.dat",
        "description": "US revenue freight carloadings, NBER, 1918-1947",
        "units": "thousands of cars",
        "frequency": "monthly",
    },
}


class NberError(RuntimeError):
    pass


def supported_series() -> list[str]:
    return sorted(SUPPORTED.keys())


def _fetch_via_fred(series_id: str, fred_id: str, vintage_utc: datetime | None) -> FetchResult:
    """Delegate to FRED fetcher and rewrap as an NBER-historical FetchResult.

    We keep the parquet payload that FRED already wrote (canonical FRED vintage
    cache) but additionally write a copy under ``vintages/nber_historical/``
    keyed by the NBER-namespaced series_id so manifests are coherent.
    """
    fr = fred_fetcher.fetch(fred_id, vintage_utc=vintage_utc)

    # Re-emit a vintage under the nber_historical publisher. Use the same
    # frame loaded back from FRED's parquet so SHA matches.
    frame = pd.read_parquet(fr.parquet_path)
    if "country_iso3" not in frame.columns:
        frame.insert(0, "country_iso3", "USA")
    if "year" not in frame.columns and "date" in frame.columns:
        frame["year"] = pd.to_datetime(frame["date"]).dt.year.astype("Int64")

    fetch_ts = utc_now()
    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=frame,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=f"https://fred.stlouisfed.org/series/{fred_id}",
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency=fr.frequency,
        units=fr.units,
        currency=None,
        start_date=fr.start_date,
        end_date=fr.end_date,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "fred_mirror_id": fred_id,
            "fred_title": fr.extra.get("title"),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            "transport": "fred_mirror",
        },
    )


def _fetch_nber_direct(series_id: str, url: str, spec: dict[str, Any]) -> FetchResult:
    """Pull a raw NBER macrohistory rectdata file (.dat or .csv).

    NBER macrohistory rectdata files are whitespace-delimited two-column
    tables: ``YYYY.fraction value`` (one observation per line) for monthly
    data, or ``YYYY value`` for annual. We parse defensively and emit a
    canonical (country_iso3, year, value) frame plus the original date
    column where reconstructable.
    """
    fetch_ts = utc_now()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    text = r.text

    rows: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            t = float(parts[0])
            v = float(parts[1])
        except ValueError:
            continue
        year = int(t)
        frac = t - year
        # NBER monthly fraction: .000=Jan, .083=Feb, ..., .917=Dec
        month = min(12, max(1, int(round(frac * 12)) + 1)) if frac > 0 else 1
        rows.append({
            "country_iso3": "USA",
            "year": year,
            "month": month,
            "date_fraction": t,
            "value": v,
        })

    if not rows:
        raise NberError(f"NBER rectdata at {url} parsed zero observations")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=1), errors="coerce"
    )
    df["year"] = df["year"].astype("Int64")

    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=url,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec.get("frequency", "monthly"),
        units=spec.get("units", "unknown"),
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) else None,
        end_date=str(int(df["year"].max())) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "transport": "nber_direct",
            "description": spec.get("description"),
        },
    )


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """Fetch a single NBER macrohistory series.

    Parameters
    ----------
    series_id
        One of the keys in ``SUPPORTED``. Series are namespaced
        ``nber_us_*`` so they don't collide with FRED's bare IDs.
    vintage_utc
        Forwarded to the FRED fetcher when the FRED mirror is used; ignored
        for direct NBER pulls (NBER files are append-only static archives).
    """
    spec = SUPPORTED.get(series_id)
    if spec is None:
        raise NberError(
            f"Unknown NBER historical series '{series_id}'. "
            f"Supported: {', '.join(supported_series())}"
        )

    fred_id = spec.get("fred_id")
    if fred_id:
        try:
            return _fetch_via_fred(series_id, fred_id, vintage_utc)
        except fred_fetcher.FredError as e:
            # Surface a clear error rather than silently falling through —
            # mirror parity is part of the contract for these ids.
            raise NberError(
                f"FRED mirror {fred_id} for {series_id} failed: {e}. "
                f"If FRED_API_KEY is set, the mirror may have been retired; "
                f"add an 'nber_csv' fallback to SUPPORTED[{series_id}]."
            ) from e

    nber_csv = spec.get("nber_csv")
    if nber_csv:
        return _fetch_nber_direct(series_id, nber_csv, spec)

    raise NberError(
        f"Series '{series_id}' has neither fred_id nor nber_csv configured."
    )


__all__ = ["fetch", "supported_series", "SUPPORTED", "NberError"]
