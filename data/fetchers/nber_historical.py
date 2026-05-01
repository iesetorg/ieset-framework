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
from datetime import datetime
import re
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
FRED_PUBLIC_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


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
        "fred_id": "M03002USM544NNBR",
        "description": "US freight cars loaded, NBER, 1918-1973",
        "units": "thousands of cars per week",
        "frequency": "monthly",
    },
}


class NberError(RuntimeError):
    pass


_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def supported_series() -> list[str]:
    return sorted(SUPPORTED.keys())


def _fetch_via_fred(series_id: str, fred_id: str, vintage_utc: datetime | None) -> FetchResult:
    """Delegate to FRED fetcher and rewrap as an NBER-historical FetchResult.

    We keep the parquet payload that FRED already wrote (canonical FRED vintage
    cache) but additionally write a copy under ``vintages/nber_historical/``
    keyed by the NBER-namespaced series_id so manifests are coherent.
    """
    try:
        fr = fred_fetcher.fetch(fred_id, vintage_utc=vintage_utc)
    except fred_fetcher.FredError as e:
        if "FRED_API_KEY not set" not in str(e) or vintage_utc is not None:
            raise
        return _fetch_via_fred_public_csv(series_id, fred_id)

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


def _fetch_via_fred_public_csv(series_id: str, fred_id: str) -> FetchResult:
    """Fallback for public, current-vintage pulls when no FRED API key is set."""
    fetch_ts = utc_now()
    r = requests.get(FRED_PUBLIC_CSV, params={"id": fred_id}, headers=UA, timeout=60)
    r.raise_for_status()

    df = pd.read_csv(io.StringIO(r.text))
    if list(df.columns[:2]) != ["DATE", fred_id]:
        raise NberError(f"Unexpected public FRED CSV schema for {fred_id}: {list(df.columns)}")
    df = df.rename(columns={"DATE": "date", fred_id: "value"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date").reset_index(drop=True)
    df.insert(0, "country_iso3", "USA")
    df["year"] = df["date"].dt.year.astype("Int64")

    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=f"{FRED_PUBLIC_CSV}?id={fred_id}",
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units="series units as reported by FRED public CSV mirror",
        currency=None,
        start_date=df["date"].min().date().isoformat() if len(df) else None,
        end_date=df["date"].max().date().isoformat() if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "fred_mirror_id": fred_id,
            "transport": "fred_public_csv",
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

    freq = spec.get("frequency", "unknown")
    tokens = _NUMBER_RE.findall(text)
    rows: list[dict[str, Any]] = []

    if freq in {"monthly", "quarterly"} and len(tokens) % 3 == 0:
        subperiods = [int(float(tok)) for tok in tokens[1::3]]
        expected_max = 12 if freq == "monthly" else 4
        if subperiods and all(1 <= sp <= expected_max for sp in subperiods):
            for i in range(0, len(tokens), 3):
                year = int(float(tokens[i]))
                subperiod = int(float(tokens[i + 1]))
                value = float(tokens[i + 2])
                month = subperiod if freq == "monthly" else (subperiod - 1) * 3 + 1
                rows.append({
                    "country_iso3": "USA",
                    "year": year,
                    "month": month,
                    "subperiod": subperiod,
                    "value": value,
                })

    if not rows and len(tokens) % 2 == 0:
        for i in range(0, len(tokens), 2):
            t = float(tokens[i])
            value = float(tokens[i + 1])
            year = int(t)
            frac = t - year
            if freq == "monthly":
                month = min(12, max(1, int(round(frac * 12)) + 1)) if frac > 0 else 1
            elif freq == "quarterly":
                quarter = min(4, max(1, int(round(frac * 4)) + 1)) if frac > 0 else 1
                month = (quarter - 1) * 3 + 1
            else:
                month = 1
            rows.append({
                "country_iso3": "USA",
                "year": year,
                "month": month,
                "date_fraction": t,
                "value": value,
            })

    if not rows:
        raise NberError(
            f"NBER rectdata at {url} parsed zero observations "
            f"(frequency={freq}, tokens={len(tokens)})"
        )

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
