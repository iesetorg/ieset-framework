"""Robert Shiller historical series fetcher (Yale).

Pulls the canonical `ie_data.xls` spreadsheet from Shiller's homepage:
    http://www.econ.yale.edu/~shiller/data.htm

Contents (monthly, US, since 1871):
    - S&P Composite Price, Dividends, Earnings
    - CPI-based deflator
    - Long interest rate (10Y)
    - Real S&P / real earnings / real dividends
    - CAPE (cyclically adjusted price/earnings)
    - Home Price Index (the monthly Case-Shiller-Shiller index back to 1890 on the 'Fig 3.1' tab)

License: academic dataset, citation required — Shiller, Irrational Exuberance.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Literal

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

DATA_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
HOME_PRICE_URL = "http://www.econ.yale.edu/~shiller/data/Fig3-1.xls"
LICENSE = "academic — Shiller; citation required"

SERIES = {
    "ie_data": ("S&P composite + CAPE + long rate (monthly, 1871-)", DATA_URL, "Data"),
    "home_price_index": ("US real home price index (annual, 1890-)", HOME_PRICE_URL, 0),
}


class ShillerError(RuntimeError):
    pass


def fetch(
    series_id: Literal["ie_data", "home_price_index"],
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in SERIES:
        raise ShillerError(f"unknown Shiller series_id '{series_id}'; one of {list(SERIES)}")
    desc, url, sheet = SERIES[series_id]

    fetch_ts = utc_now()
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    sheet_name = sheet if isinstance(sheet, str) else xls.sheet_names[sheet]

    if series_id == "ie_data":
        # The Data tab has a header on row 7 (0-indexed); some revisions on row 8.
        # Read aggressively and drop non-numeric header leftovers.
        df = xls.parse(sheet_name, skiprows=7)
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
        # Shiller's date column is decimal year like 1871.01 (Jan 1871), 1871.02 (Feb).
        date_col = next((c for c in df.columns if str(c).strip().lower().startswith("date")), None)
        if date_col is None:
            raise ShillerError("couldn't locate 'Date' column in ie_data")
        df = df.rename(columns={date_col: "decimal_year"})
        df = df[pd.to_numeric(df["decimal_year"], errors="coerce").notna()].copy()
        df["decimal_year"] = pd.to_numeric(df["decimal_year"])
        df["year"] = df["decimal_year"].astype(int)
        df["month"] = ((df["decimal_year"] - df["year"]) * 100).round().astype(int)
    else:  # home_price_index
        # Fig3-1 layout: 6 header rows (title + legend), data starts row 7.
        # Column 0 is the year (annual series), column 1 is the real home
        # price index (base 1890=100). Columns 4/5 are the monthly series
        # since 1953 which we ignore here.
        raw = xls.parse(sheet_name, header=None)
        year = pd.to_numeric(raw[0], errors="coerce")
        idx = pd.to_numeric(raw[1], errors="coerce")
        mask = year.notna() & idx.notna() & (year >= 1800) & (year <= 2100)
        df = pd.DataFrame({"year": year[mask].astype(int), "real_home_price_index": idx[mask].astype(float)})
        df = df.sort_values("year").drop_duplicates(subset="year").reset_index(drop=True)

    path_out, sha = write_vintage(
        publisher="shiller",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="shiller",
        series_id=series_id,
        source_url=url,
        methodology_url="http://www.econ.yale.edu/~shiller/data.htm",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly" if series_id == "ie_data" else "annual",
        units="index / ratio / decimal percent depending on column",
        currency="USD",
        start_date=str(df["year"].min()) if "year" in df.columns and len(df) else None,
        end_date=str(df["year"].max()) if "year" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "description": desc,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
