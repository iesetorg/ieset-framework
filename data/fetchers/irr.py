"""Ilzetzki-Reinhart-Rogoff exchange rate regime classification.

Three xlsx files on Ilzetzki's personal site, hosted via wix CDN.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Literal

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic — Ilzetzki, Reinhart & Rogoff; citation required"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}

SERIES = {
    "era_classification_monthly_1940_2019":
        ("https://www.ilzetzki.com/_files/ugd/b3763a_242513d0fba24aa1a64be41c8f73d887.xlsx",
         "Monthly exchange rate regime classification 1940-2019"),
    "unified_market_analysis_1946_2021":
        ("https://www.ilzetzki.com/_files/ugd/b3763a_48a9a40476c6465da949a3456b1b3e4c.xlsx",
         "Unified-market analysis 1946-2021 (dual/multiple exchange rates)"),
    "anchor_currency_monthly_1946_2019":
        ("https://www.ilzetzki.com/_files/ugd/b3763a_7b72377cfe184f72ba0ad77dabbabae0.xlsx",
         "Anchor currency monthly classification 1946-2019"),
}


class IrrError(RuntimeError):
    pass


def fetch(
    series_id: Literal["era_classification_monthly_1940_2019", "unified_market_analysis_1946_2021", "anchor_currency_monthly_1946_2019"],
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in SERIES:
        raise IrrError(f"unknown IRR series_id {series_id!r}; one of {list(SERIES)}")
    url, desc = SERIES[series_id]

    fetch_ts = utc_now()
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))

    # Collect every sheet into a single annotated long frame; IRR spreads
    # data across per-regime sheets, we want the full panel.
    frames = []
    for sheet in xls.sheet_names:
        try:
            df = xls.parse(sheet)
        except Exception:
            continue
        df["__sheet"] = sheet
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    path_out, sha = write_vintage(
        publisher="irr",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="irr",
        series_id=series_id,
        source_url=url,
        methodology_url="https://www.ilzetzki.com/irr-data",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="monthly",
        units="regime classification codes per IRR (2019) codebook",
        currency=None,
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "description": desc,
            "sheets": xls.sheet_names,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
