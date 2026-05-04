"""US Bureau of Labor Statistics (BLS) Public API v2.

Endpoint: https://api.bls.gov/publicAPI/v2
Auth: optional (free registration for higher rate limits). Without key: 25
queries/day per IP, 10 series per query, 10 years max. With key: 500 queries/day.

BLS covers US labor at higher resolution than FRED's mirror: CPI detailed,
PPI by industry, employment by state/industry, earnings, productivity.
"""
from __future__ import annotations

import io
import os
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://api.bls.gov/publicAPI/v2"
QCEW_BASE = "https://data.bls.gov/cew/data/api"
LICENSE = "public_domain"


class BlsError(RuntimeError):
    pass


STATE_AREA_FIPS = [
    "01000", "02000", "04000", "05000", "06000", "08000", "09000", "10000",
    "11000", "12000", "13000", "15000", "16000", "17000", "18000", "19000",
    "20000", "21000", "22000", "23000", "24000", "25000", "26000", "27000",
    "28000", "29000", "30000", "31000", "32000", "33000", "34000", "35000",
    "36000", "37000", "38000", "39000", "40000", "41000", "42000", "44000",
    "45000", "46000", "47000", "48000", "49000", "50000", "51000", "53000",
    "54000", "55000", "56000",
]


def _qcew_years() -> range:
    start = int(os.environ.get("BLS_QCEW_START_YEAR", "1990"))
    end = int(os.environ.get("BLS_QCEW_END_YEAR", "2024"))
    if start > end:
        raise BlsError("BLS_QCEW_START_YEAR must be <= BLS_QCEW_END_YEAR")
    return range(start, end + 1)


def _fetch_qcew_year(year: int, industry_code: str) -> pd.DataFrame:
    url = f"{QCEW_BASE}/{year}/a/industry/{industry_code}.csv"
    r = requests.get(url, timeout=60)
    if r.status_code == 404:
        return pd.DataFrame()
    r.raise_for_status()
    text = r.text.strip()
    if not text:
        return pd.DataFrame()
    df = pd.read_csv(io.StringIO(text), dtype=str)
    state_set = set(STATE_AREA_FIPS)
    ownership_code = "5" if industry_code == "722" else "0"
    mask = (
        df["area_fips"].isin(state_set)
        & (df["own_code"] == ownership_code)
        & (df["industry_code"] == industry_code)
    )
    return df.loc[mask].copy()


def _fetch_qcew_panel(series_id: str, *, fetch_ts: datetime) -> FetchResult:
    industry_code = {
        "QCEW_state_total_employment_panel": "10",
        "QCEW_state_NAICS72_employment_panel": "722",
        "QCEW_state_NAICS722_employment_panel": "722",
    }.get(series_id)
    if industry_code is None:
        raise BlsError(f"unknown QCEW panel {series_id!r}")

    frames: list[pd.DataFrame] = []
    for year in _qcew_years():
        df = _fetch_qcew_year(year, industry_code)
        if not df.empty:
            frames.append(df)
    if not frames:
        raise BlsError(f"BLS QCEW {series_id}: no observations")

    out = pd.concat(frames, ignore_index=True)
    numeric_cols = [
        "annual_avg_estabs", "annual_avg_emplvl", "total_annual_wages",
        "taxable_annual_wages", "annual_contributions", "annual_avg_wkly_wage",
        "avg_annual_pay",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "year" in out.columns:
        out["year"] = pd.to_numeric(out["year"], errors="coerce").astype("Int64")

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{QCEW_BASE}/{{year}}/a/industry/{industry_code}.csv",
        methodology_url="https://www.bls.gov/cew/downloadable-data-files.htm",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units="establishments, employment, wages, and pay by QCEW area/industry",
        currency="USD",
        start_date=str(int(out["year"].min())) if len(out) else None,
        end_date=str(int(out["year"].max())) if len(out) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "qcew_year_start": min(_qcew_years()),
            "qcew_year_end": max(_qcew_years()),
            "qcew_area_count": len(STATE_AREA_FIPS),
            "qcew_industry_code": industry_code,
        },
    )


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> FetchResult:
    """series_id: BLS series code (e.g., 'CUUR0000SA0' = CPI-U all items)."""
    fetch_ts = utc_now()
    if series_id.startswith("QCEW_state_"):
        return _fetch_qcew_panel(series_id, fetch_ts=fetch_ts)

    payload: dict = {"seriesid": [series_id]}
    if start_year:
        payload["startyear"] = str(start_year)
    if end_year:
        payload["endyear"] = str(end_year)
    key = os.environ.get("BLS_API_KEY")
    if key:
        payload["registrationkey"] = key
    r = requests.post(
        f"{BASE}/timeseries/data/",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    doc = r.json()
    if doc.get("status") != "REQUEST_SUCCEEDED":
        raise BlsError(f"BLS {series_id} failed: {doc.get('status')} — {doc.get('message')}")
    series_list = doc.get("Results", {}).get("series", [])
    if not series_list:
        raise BlsError(f"BLS {series_id}: no series returned")
    data = series_list[0].get("data", [])
    if not data:
        raise BlsError(f"BLS {series_id}: no observations")
    df = pd.DataFrame(data)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="bls",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="bls",
        series_id=series_id,
        source_url=f"{BASE}/timeseries/data/{series_id}",
        methodology_url=f"https://data.bls.gov/timeseries/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units="per series (index, rate, dollars)",
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) else None,
        end_date=str(int(df["year"].max())) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "bls_registration_key_used": bool(key),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
