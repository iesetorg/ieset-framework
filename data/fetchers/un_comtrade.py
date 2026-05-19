"""UN Comtrade API fetcher.

This fetcher targets the specific Comtrade shapes used by IESET's product-line,
CBAM, and infant-industry specs. It keeps requests bounded by default because
the public Comtrade API has row and rate limits; set ``UN_COMTRADE_KEY`` for a
registered API key when available.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://comtradeapi.un.org/data/v1/get/C/A/HS"
LICENSE = "UN Comtrade terms — citation required"
METHOD_URL = "https://comtradeapi.un.org/data/doc/api/"

DEFAULT_REPORTERS = (
    "842,156,276,392,410,826,251,381,036,124,484,076,699,710,356,704,360,764,458,702"
)
HS2_CORE = (
    "01,02,03,04,05,06,07,08,09,10,11,12,15,16,17,18,19,20,21,22,23,24,"
    "25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,"
    "47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,"
    "68,69,70,71,72,73,74,75,76,78,79,80,81,82,83,84,85,86,87,88,89,"
    "90,91,92,93,94,95,96,97"
)
CBAM_CODES = "72,76,25,31"

SERIES: dict[str, dict[str, Any]] = {
    "HS72_HS76_HS25_HS31": {
        "cmd_code": CBAM_CODES,
        "flow_code": "M,X",
        "reporter_code": "918",
        "desc": "CBAM-relevant HS2 product groups, EU aggregate, imports and exports",
    },
    "HS72_HS76_HS25_HS31_volume": {
        "cmd_code": CBAM_CODES,
        "flow_code": "M,X",
        "reporter_code": "918",
        "desc": "CBAM-relevant HS2 product groups with net weight fields",
    },
    "export_value_by_sector": {
        "cmd_code": HS2_CORE,
        "flow_code": "X",
        "reporter_code": DEFAULT_REPORTERS,
        "desc": "HS2 merchandise export values for a broad reporter panel",
    },
    "hs_two_digit": {
        "cmd_code": HS2_CORE,
        "flow_code": "X,M",
        "reporter_code": DEFAULT_REPORTERS,
        "desc": "HS2 merchandise trade values for a broad reporter panel",
    },
}


class ComtradeError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "IESET data fetcher (contact: repository maintainers)"}
    key = os.environ.get("UN_COMTRADE_KEY")
    if key:
        headers["Ocp-Apim-Subscription-Key"] = key
    return headers


def _periods(start_year: int, end_year: int, chunk: int) -> list[str]:
    years = [str(y) for y in range(start_year, end_year + 1)]
    return [",".join(years[i : i + chunk]) for i in range(0, len(years), chunk)]


def _fetch_chunk(params: dict[str, str]) -> list[dict[str, Any]]:
    r = requests.get(BASE, params=params, headers=_headers(), timeout=180)
    if r.status_code == 429:
        time.sleep(8)
        r = requests.get(BASE, params=params, headers=_headers(), timeout=180)
    if r.status_code >= 400:
        raise ComtradeError(f"UN Comtrade HTTP {r.status_code}: {r.text[:500]}")
    payload = r.json()
    if isinstance(payload, dict) and payload.get("error"):
        raise ComtradeError(f"UN Comtrade API error: {payload.get('error')}")
    if isinstance(payload, dict):
        return payload.get("data") or payload.get("dataset") or []
    if isinstance(payload, list):
        return payload
    return []


def _normalise(rows: list[dict[str, Any]], series_id: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    rename = {
        "period": "year",
        "reporterISO": "country_iso3",
        "reporterDesc": "country_name",
        "partnerISO": "partner_iso3",
        "partnerDesc": "partner_name",
        "cmdCode": "commodity_code",
        "cmdDesc": "commodity",
        "flowCode": "flow_code",
        "flowDesc": "flow",
        "primaryValue": "value",
        "netWgt": "net_weight_kg",
        "qty": "quantity",
        "qtyUnitAbbr": "quantity_unit",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for col in ("value", "net_weight_kg", "quantity"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "country_iso3" in df.columns:
        df["country_iso3"] = df["country_iso3"].astype("string").str.upper()
    df["series_id"] = series_id
    keep_first = [
        c
        for c in (
            "series_id",
            "country_iso3",
            "country_name",
            "year",
            "partner_iso3",
            "partner_name",
            "commodity_code",
            "commodity",
            "flow_code",
            "flow",
            "value",
            "net_weight_kg",
            "quantity",
            "quantity_unit",
        )
        if c in df.columns
    ]
    rest = [c for c in df.columns if c not in keep_first]
    df = df[keep_first + rest]
    if "year" in df.columns:
        df = df.dropna(subset=["year"])
    if "value" in df.columns:
        df = df.dropna(subset=["value"], how="all")
    if {"country_iso3", "year"}.issubset(df.columns):
        df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    return df


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    start_year: int = 2010,
    end_year: int = 2024,
    reporter_code: str | None = None,
    period_chunk: int = 3,
) -> FetchResult:
    if series_id in {"product_lines", "unique_hs6_products", "export_product_concentration"}:
        raise ComtradeError(
            f"{series_id} requires a derived HS6 product-line builder; use WITS product-line "
            "indicators for the current broad panel, or run a key-backed Comtrade HS6 build."
        )
    if series_id not in SERIES:
        raise ComtradeError(f"unsupported UN Comtrade series_id {series_id!r}; known: {sorted(SERIES)}")

    fetch_ts = utc_now()
    spec = SERIES[series_id]
    rows: list[dict[str, Any]] = []
    for period in _periods(start_year, end_year, period_chunk):
        params = {
            "cmdCode": spec["cmd_code"],
            "flowCode": spec["flow_code"],
            "partnerCode": "0",
            "reporterCode": reporter_code or spec["reporter_code"],
            "period": period,
            "includeDesc": "true",
        }
        rows.extend(_fetch_chunk(params))
        time.sleep(0.8)

    df = _normalise(rows, series_id)
    if df.empty:
        raise ComtradeError(f"UN Comtrade returned no rows for {series_id}")

    path, sha = write_vintage(
        publisher="un_comtrade",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="un_comtrade",
        series_id=series_id,
        source_url=BASE,
        methodology_url=METHOD_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="current USD value; kg where volume/weight fields are present",
        currency="USD",
        start_date=str(int(df["year"].min())) if "year" in df.columns else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns else None,
        sha256=sha,
        parquet_path=path,
        extra={
            "desc": spec["desc"],
            "cmd_code": spec["cmd_code"],
            "flow_code": spec["flow_code"],
            "reporter_code": reporter_code or spec["reporter_code"],
            "partner_code": "0",
            "start_year": start_year,
            "end_year": end_year,
            "api_key_used": bool(os.environ.get("UN_COMTRADE_KEY")),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            "columns": list(df.columns),
        },
    )
