"""Destatis (Statistisches Bundesamt, Germany) GENESIS-Online REST 2020 fetcher.

Endpoint:  https://www-genesis.destatis.de/genesisWS/rest/2020/data/tablefile
Docs:      https://www-genesis.destatis.de/genesis/online?Menu=Webservice
License:   Destatis open data clause (treated as public_domain-equivalent, with
           attribution requested).

Auth: free registration grants username/password (env GENESIS_USER / GENESIS_PASS).
Many tables are also accessible with the public guest account
(username='GAST', empty password) — we default to that so the fetcher works
out-of-the-box.

Series identifier convention: Destatis table number (e.g. '81000-0001'). For
convenience, the SUPPORTED registry below also accepts the bare table family
prefix (e.g. '81000') and resolves it to the canonical sub-table.

Strategy: prefer the GENESIS REST 'tablefile' endpoint with format=csv, which
returns a flat-csv variant that pandas can parse. We rate-limit at 500 ms
between outgoing requests per the polite-client guidance in the Destatis terms.
"""
from __future__ import annotations

import io
import os
import re
import threading
import time
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www-genesis.destatis.de/genesisWS/rest/2020/data/tablefile"
LICENSE = "public_domain"  # Destatis open data clause; attribution requested

# 500 ms rate limit between requests (process-wide, thread-safe).
_RATE_LIMIT_SECONDS = 0.5
_RATE_LOCK = threading.Lock()
_LAST_CALL_TS = 0.0


# Module-level registry of supported series. Values are the canonical
# Destatis table identifiers (typically <family>-<sub>).
SUPPORTED: dict[str, dict[str, str]] = {
    # Industrial production index — monthly, by economic activity.
    "42153": {
        "table": "42153-0001",
        "title": "Index of production in industry (monthly)",
        "frequency": "monthly",
        "currency": None,
        "units": "index 2021=100",
    },
    "42153-0001": {
        "table": "42153-0001",
        "title": "Index of production in industry (monthly)",
        "frequency": "monthly",
        "currency": None,
        "units": "index 2021=100",
    },
    # Consumer price index — monthly, all-items + sub-indices.
    "61111": {
        "table": "61111-0001",
        "title": "Consumer Price Index (monthly, all-items)",
        "frequency": "monthly",
        "currency": None,
        "units": "index 2020=100",
    },
    "61111-0001": {
        "table": "61111-0001",
        "title": "Consumer Price Index (monthly, all-items)",
        "frequency": "monthly",
        "currency": None,
        "units": "index 2020=100",
    },
    # Gross domestic product — quarterly aggregates (price-, calendar-, and
    # seasonally adjusted; chain-linked).
    "81000": {
        "table": "81000-0001",
        "title": "GDP and components (quarterly)",
        "frequency": "quarterly",
        "currency": "EUR",
        "units": "EUR million / index",
    },
    "81000-0001": {
        "table": "81000-0001",
        "title": "GDP and components (quarterly)",
        "frequency": "quarterly",
        "currency": "EUR",
        "units": "EUR million / index",
    },
    # Earnings/wages — quarterly nominal+real.
    "62121": {
        "table": "62121-0001",
        "title": "Index of nominal and real earnings (quarterly)",
        "frequency": "quarterly",
        "currency": "EUR",
        "units": "index 2020=100",
    },
    "62121-0001": {
        "table": "62121-0001",
        "title": "Index of nominal and real earnings (quarterly)",
        "frequency": "quarterly",
        "currency": "EUR",
        "units": "index 2020=100",
    },
    # Employment / labour-force participation (Mikrozensus subset).
    "13231": {
        "table": "13231-0001",
        "title": "Labour-force participation rate (annual, Mikrozensus)",
        "frequency": "annual",
        "currency": None,
        "units": "percent",
    },
    "13231-0001": {
        "table": "13231-0001",
        "title": "Labour-force participation rate (annual, Mikrozensus)",
        "frequency": "annual",
        "currency": None,
        "units": "percent",
    },
    # Semantic-name aliases for spec citations using descriptive labels rather
    # than table IDs. Each maps to the closest existing GENESIS table.
    "mikrozensus": {
        "table": "12211-0001",
        "title": "Mikrozensus — population by labour-force status (annual)",
        "frequency": "annual",
        "currency": None,
        "units": "thousands of persons",
    },
    "arbeitsmarkt": {
        "table": "13231-0001",
        "title": "Labour-market overview — participation, employment, unemployment",
        "frequency": "annual",
        "currency": None,
        "units": "percent / thousands",
    },
    "erwerbstaetige": {
        "table": "81000-0021",
        "title": "Persons in employment (Erwerbstätige), national accounts",
        "frequency": "quarterly",
        "currency": None,
        "units": "thousands of persons",
    },
    "bevoelkerung": {
        "table": "12411-0001",
        "title": "Population (Bevölkerung) — annual stock",
        "frequency": "annual",
        "currency": None,
        "units": "thousands of persons",
    },
    "baufertigstellungen": {
        "table": "31121-0001",
        "title": "Completed dwellings (Baufertigstellungen) — annual",
        "frequency": "annual",
        "currency": None,
        "units": "number of dwellings",
    },
    "wohngebaeude_baujahr": {
        "table": "31231-0001",
        "title": "Housing stock by year of construction (Wohngebäude nach Baujahr)",
        "frequency": "annual",
        "currency": None,
        "units": "number of buildings",
    },
    "VSE": {
        "table": "62361-0001",
        "title": "Verdienststrukturerhebung — earnings-structure survey (4-yearly)",
        "frequency": "quadrennial",
        "currency": "EUR",
        "units": "EUR / hour, EUR / month",
    },
}


class DestatisError(RuntimeError):
    pass


def _rate_limit() -> None:
    global _LAST_CALL_TS
    with _RATE_LOCK:
        now = time.monotonic()
        delta = now - _LAST_CALL_TS
        if delta < _RATE_LIMIT_SECONDS:
            time.sleep(_RATE_LIMIT_SECONDS - delta)
        _LAST_CALL_TS = time.monotonic()


def _credentials() -> tuple[str, str]:
    """Return (username, password). Use GENESIS_USER/PASS if both set, else GAST."""
    user = os.environ.get("GENESIS_USER")
    pwd = os.environ.get("GENESIS_PASS")
    if user and pwd:
        return user, pwd
    # GAST = public guest account; password is empty string.
    return "GAST", ""


def _request_table(table: str, *, area: str = "all") -> str:
    """Hit GENESIS tablefile endpoint and return the raw text body."""
    user, pwd = _credentials()
    params = {
        "username": user,
        "password": pwd,
        "name": table,
        "area": area,
        "format": "csv",
        "language": "en",
        "compress": "false",
    }
    _rate_limit()
    r = requests.get(BASE, params=params, timeout=120)
    r.raise_for_status()
    text = r.text
    # GENESIS reports errors as a small JSON body even on HTTP 200.
    head = text.lstrip()[:64].lower()
    if head.startswith("{") and ('"code"' in text[:512] or '"status"' in text[:512]):
        # Try to surface the embedded message.
        raise DestatisError(f"Destatis error for table {table}: {text[:300]}")
    if not text.strip():
        raise DestatisError(f"Destatis returned empty body for table {table}")
    return text


def _parse_genesis_csv(text: str) -> pd.DataFrame:
    """Parse the GENESIS flat-csv into a tidy DataFrame.

    Genesis flat CSVs are semicolon-delimited; the first non-empty section
    contains an obs grid. We strip leading metadata blocks (separated by
    blank lines) and read the last block, which is conventionally the data.
    """
    # Genesis often emits a metadata preamble followed by a blank line and
    # then the actual table. Try semicolon delimiter first.
    blocks = re.split(r"\r?\n\r?\n+", text.strip())
    last = blocks[-1] if blocks else text
    df: pd.DataFrame | None = None
    for sep in (";", ",", "\t"):
        try:
            candidate = pd.read_csv(io.StringIO(last), sep=sep, engine="python", on_bad_lines="skip")
        except Exception:
            continue
        if candidate.shape[1] >= 2 and len(candidate) > 0:
            df = candidate
            break
    if df is None or df.empty:
        # Fall back to whole-document parse.
        df = pd.read_csv(io.StringIO(text), sep=";", engine="python", on_bad_lines="skip")
    if df.empty:
        raise DestatisError("Destatis CSV parsed empty")
    # Best-effort column normalisation: lowercase, ascii-safe.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    area: str = "all",
) -> FetchResult:
    """Fetch a Destatis GENESIS table as a tidy DataFrame.

    series_id: Destatis table id, e.g. '81000-0001' (or family prefix '81000').
               Free-form table ids not in SUPPORTED are also passed through.
    area:      'all' (default; default user area), 'free', 'user'.
    """
    fetch_ts = utc_now()
    meta = SUPPORTED.get(series_id, {})
    table = meta.get("table") or series_id

    text = _request_table(table, area=area)
    df = _parse_genesis_csv(text)

    # Heuristic period detection — Genesis exposes time as a column whose name
    # contains 'Jahr', 'Year', 'Zeit' or 'time'.
    period_col = next(
        (c for c in df.columns if re.search(r"jahr|year|zeit|time|period|monat|quartal", c, re.I)),
        None,
    )
    if period_col and period_col != "period":
        df = df.rename(columns={period_col: "period"})
    value_col = next(
        (c for c in df.columns if re.search(r"^value$|wert|index", c, re.I)),
        None,
    )
    if value_col and value_col != "value":
        df = df.rename(columns={value_col: "value"})
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="destatis",
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

    user, _ = _credentials()
    return FetchResult(
        publisher="destatis",
        series_id=series_id,
        source_url=f"{BASE}?name={table}&format=csv&area={area}",
        methodology_url=f"https://www-genesis.destatis.de/genesis/online?operation=table&code={table}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency", "unknown"),
        units=meta.get("units", "per table metadata"),
        currency=meta.get("currency"),
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "table": table,
            "title": meta.get("title", ""),
            "auth_user": user,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
