"""Jordà-Schularick-Taylor Macrohistory Database.

17 advanced economies, 1870-present, macrofinancial variables (GDP, inflation,
short/long rates, money aggregates, bank assets, credit, asset prices, housing).

Release 6 (latest, 2024). Single xlsx, static URL.

Essential for long-run monetary + financial hypotheses the refinements cite:
fiat_expansion_erodes_currency_purchasing_power_long_run, and any cross-country
analysis of pre-1971 monetary regimes.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
LICENSE = "academic — Jordà-Schularick-Taylor; citation required"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


def fetch(series_id: str = "jst_r6", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    r = requests.get(URL, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    # JST R6 ships the main dataset on the 'Data' sheet.
    sheet = next((s for s in xls.sheet_names if s.strip().lower() == "data"), xls.sheet_names[0])
    df = xls.parse(sheet)
    rename = {c: c.strip().lower() for c in df.columns if isinstance(c, str)}
    df = df.rename(columns=rename)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "iso" in df.columns:
        df = df.rename(columns={"iso": "country_iso3"})
    elif "country" in df.columns and "country_iso3" not in df.columns:
        # JST uses full country names not ISO codes in some releases; keep as-is but tag.
        df["country_name"] = df["country"]

    path_out, sha = write_vintage(
        publisher="jst",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="jst",
        series_id=series_id,
        source_url=URL,
        methodology_url="https://www.macrohistory.net/database/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="mixed (see variable docs)",
        currency=None,
        start_date=str(int(df["year"].min())) if "year" in df.columns and len(df) else None,
        end_date=str(int(df["year"].max())) if "year" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "release": "R6",
            "sheet_used": sheet,
            "n_columns": len(df.columns),
            "columns_sample": list(df.columns)[:30],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
