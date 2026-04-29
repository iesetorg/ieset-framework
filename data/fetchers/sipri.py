"""SIPRI Military Expenditure Database.

Stockholm International Peace Research Institute. Annual military spending
for 170+ countries 1948-present. Static xlsx.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1948-2023.xlsx"
LICENSE = "academic/press — SIPRI; attribution required"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}

SHEETS_TO_PARSE = [
    "Constant (2022) US$",    # real values
    "Current US$",            # nominal
    "Share of GDP",           # % GDP
    "Per capita",             # per-capita real
]


def fetch(series_id: str = "milex_constant_usd", *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id picks which sheet: 'constant_usd' | 'current_usd' | 'share_gdp' | 'per_capita'."""
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    target_sheet = None
    alias = series_id.lower().replace("-", "_")
    for s in xls.sheet_names:
        if "constant" in s.lower() and "constant_usd" in alias:
            target_sheet = s; break
        if "current" in s.lower() and "current_usd" in alias:
            target_sheet = s; break
        if "share" in s.lower() and "gdp" in alias:
            target_sheet = s; break
        if "per capita" in s.lower() and "per_capita" in alias:
            target_sheet = s; break
    if target_sheet is None:
        # default: constant USD if present, else first data-looking sheet
        target_sheet = next((s for s in xls.sheet_names if "constant" in s.lower()), xls.sheet_names[1] if len(xls.sheet_names) > 1 else xls.sheet_names[0])

    # SIPRI sheets usually have a 5-row preamble before the country panel.
    df = xls.parse(target_sheet, skiprows=5)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    # First column is country, remainder are years
    if df.columns[0] != "Country":
        df = df.rename(columns={df.columns[0]: "Country"})
    # Melt to long form
    year_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(type(c)) or (isinstance(c, (int, float)) and 1900 < c < 2100) or (isinstance(c, str) and c.isdigit())]
    if year_cols:
        long = df.melt(id_vars=["Country"], value_vars=year_cols, var_name="year", value_name="value")
        long["year"] = pd.to_numeric(long["year"], errors="coerce").astype("Int64")
        long["value"] = pd.to_numeric(long["value"], errors="coerce")
        long = long.dropna(subset=["year", "Country"]).reset_index(drop=True)
        df = long

    path_out, sha = write_vintage(
        publisher="sipri",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="sipri",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://www.sipri.org/databases/milex",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="depends on sheet: constant 2022 USD / current USD / % GDP / per capita real",
        currency="USD" if "usd" in alias else None,
        start_date=str(int(df["year"].min())) if "year" in df.columns and len(df) else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sheet_used": target_sheet,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
