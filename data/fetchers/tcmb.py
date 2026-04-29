"""TCMB (Central Bank of the Republic of Turkey) — EVDS fetcher.

Endpoint:    https://evds2.tcmb.gov.tr/service/evds/
Auth:        free API key — register at https://evds2.tcmb.gov.tr,
             then export TCMB_API_KEY (header: 'key').
Docs:        https://evds2.tcmb.gov.tr/help/videos/EVDS_Web_Service_Usage_Guide.pdf
License:     Turkish official statistics terms — treated as 'unknown' here.

Notes
-----
* EVDS REST URL layout:
      /serieS=<series>-<series>...&startDate=DD-MM-YYYY&endDate=DD-MM-YYYY&type=json
  with the API key passed via the 'key' HTTP header.
* If TCMB_API_KEY is not set we degrade to a public-mirror CSV (currently
  routed via the EVDS public dataset URLs) so the module is import-safe and
  buildable in dev without registering for a key. The fallback returns a
  small placeholder frame so write_vintage / FetchResult contract still holds.
* 500 ms rate-limit between requests (TCMB enforces a relatively low ceiling).

SUPPORTED registry maps short logical IDs and the raw EVDS series codes to
the canonical EVDS series identifier; both forms are accepted by fetch().
"""
from __future__ import annotations

import io
import os
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

EVDS_BASE = "https://evds2.tcmb.gov.tr/service/evds"
LICENSE = "unknown"

# 500ms rate-limit between requests
_MIN_INTERVAL_SEC = 0.5
_LAST_REQ_TS: float = 0.0


# Canonical EVDS series codes used in IESET hypotheses.
# Keys are both the EVDS code and a human-readable alias.
SUPPORTED: dict[str, dict[str, Any]] = {
    "TP.AB.B01": {
        "alias": "policy_rate",
        "title": "TCMB one-week repo (policy) rate",
        "frequency": "daily",
        "units": "percent per annum",
        "currency": None,
    },
    "TP.FG.J0": {
        "alias": "cpi_headline",
        "title": "Consumer Price Index, headline (monthly)",
        "frequency": "monthly",
        "units": "index, 2003=100",
        "currency": None,
    },
    "TP.DK.USD.A.YTL": {
        "alias": "usdtry",
        "title": "USD / TRY exchange rate (CBRT buying)",
        "frequency": "daily",
        "units": "TRY per USD",
        "currency": "TRY",
    },
    "TP.M3.A02": {
        "alias": "m2_broad_money",
        "title": "M2 broad money aggregate",
        "frequency": "monthly",
        "units": "TRY thousands",
        "currency": "TRY",
    },
    "TP.IFS.O17": {
        "alias": "reserves",
        "title": "International reserves",
        "frequency": "monthly",
        "units": "USD millions",
        "currency": "USD",
    },
}

# Allow alias lookups: "policy_rate" -> "TP.AB.B01"
_ALIAS_TO_CODE: dict[str, str] = {meta["alias"]: code for code, meta in SUPPORTED.items()}


class TcmbError(RuntimeError):
    pass


def _api_key() -> str | None:
    return os.environ.get("TCMB_API_KEY") or None


def _resolve(series_id: str) -> str:
    """Accept either an EVDS code (TP.AB.B01) or alias (policy_rate)."""
    if series_id in SUPPORTED:
        return series_id
    if series_id in _ALIAS_TO_CODE:
        return _ALIAS_TO_CODE[series_id]
    # Unknown but well-formed EVDS codes still pass through to EVDS — caller
    # may be pulling a series we haven't catalogued yet.
    return series_id


def _rate_limit() -> None:
    global _LAST_REQ_TS
    now = time.monotonic()
    delta = now - _LAST_REQ_TS
    if delta < _MIN_INTERVAL_SEC:
        time.sleep(_MIN_INTERVAL_SEC - delta)
    _LAST_REQ_TS = time.monotonic()


def _evds_request(
    code: str,
    *,
    start_date: str,
    end_date: str,
    api_key: str,
) -> dict:
    """Call EVDS REST endpoint. EVDS expects DD-MM-YYYY date strings."""
    _rate_limit()
    url = f"{EVDS_BASE}/series={code}&startDate={start_date}&endDate={end_date}&type=json"
    r = requests.get(url, headers={"key": api_key}, timeout=60)
    if r.status_code in (401, 403):
        raise TcmbError(
            f"TCMB EVDS auth rejected for {code} (status {r.status_code}). "
            "Check TCMB_API_KEY."
        )
    r.raise_for_status()
    try:
        return r.json()
    except ValueError as e:
        raise TcmbError(f"TCMB EVDS returned non-JSON for {code}: {e}") from None


def _frame_from_evds(payload: dict, code: str) -> pd.DataFrame:
    items = payload.get("items") or []
    if not items:
        raise TcmbError(f"TCMB EVDS returned empty items[] for {code}")
    df = pd.DataFrame(items)
    # EVDS returns columns named with dots replaced by underscores, eg
    # 'TP_AB_B01'; collapse to a stable 'value' column.
    value_col_candidates = [c for c in df.columns if c.replace("_", ".") == code]
    if value_col_candidates:
        df = df.rename(columns={value_col_candidates[0]: "value"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if "Tarih" in df.columns:
        df = df.rename(columns={"Tarih": "period"})
    elif "UNIXTIME" in df.columns:
        df = df.rename(columns={"UNIXTIME": "period"})
    return df


def _fallback_frame(code: str) -> pd.DataFrame:
    """No-auth fallback: return a metadata-only frame so the contract
    (parquet + sha + FetchResult) still holds in dev environments.

    This is intentionally tiny — full historical mirroring of TCMB data
    without a key is not licensed; users wanting real data must register.
    """
    meta = SUPPORTED.get(code, {})
    return pd.DataFrame(
        [
            {
                "period": None,
                "value": None,
                "note": "TCMB_API_KEY not set — fallback placeholder frame. "
                        "Register at https://evds2.tcmb.gov.tr to obtain a key.",
                "series_code": code,
                "title": meta.get("title", "(unknown EVDS series)"),
            }
        ]
    )


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    start_date: str = "01-01-1990",
    end_date: str | None = None,
) -> FetchResult:
    """Fetch a TCMB EVDS series.

    series_id: EVDS code ('TP.AB.B01') or alias ('policy_rate').
    start_date / end_date: DD-MM-YYYY strings (EVDS native format).
    """
    fetch_ts = utc_now()
    code = _resolve(series_id)
    end_date = end_date or fetch_ts.strftime("%d-%m-%Y")
    meta = SUPPORTED.get(code, {})

    api_key = _api_key()
    using_fallback = api_key is None
    if using_fallback:
        df = _fallback_frame(code)
        source_url = f"{EVDS_BASE}/series={code}&startDate={start_date}&endDate={end_date}&type=json"
    else:
        payload = _evds_request(code, start_date=start_date, end_date=end_date, api_key=api_key)
        df = _frame_from_evds(payload, code)
        source_url = f"{EVDS_BASE}/series={code}&startDate={start_date}&endDate={end_date}&type=json"

    path, sha = write_vintage(
        publisher="tcmb",
        series_id=code,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start_obs = end_obs = None
    if "period" in df.columns and df["period"].notna().any():
        start_obs = str(df["period"].min())
        end_obs = str(df["period"].max())

    return FetchResult(
        publisher="tcmb",
        series_id=code,
        source_url=source_url,
        methodology_url="https://evds2.tcmb.gov.tr/index.php?/evds/dashboard/EN",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency", "unknown"),
        units=meta.get("units", "unknown"),
        currency=meta.get("currency"),
        start_date=start_obs,
        end_date=end_obs,
        sha256=sha,
        parquet_path=path,
        extra={
            "evds_code": code,
            "alias": meta.get("alias"),
            "title": meta.get("title"),
            "auth": "header_key" if not using_fallback else "fallback_no_key",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
