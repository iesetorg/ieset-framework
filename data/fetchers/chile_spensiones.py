"""Superintendencia de Pensiones de Chile (AFP system) — manual-drop.

Source URL (browser):
    https://www.spensiones.cl/portal/institucional/594/w3-propertyvalue-5793.html
    → Series Estadísticas → individual tables

AFP forced-saving pension system data for the Chicago-Boys-era chile_afp
policy (refinement D.2.9 context). Essential for welfare-architecture
hypothesis.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "afp_statistics", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("chile_spensiones", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(publisher="chile_spensiones", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="chile_spensiones", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.spensiones.cl/portal/institucional/594/w3-channel.html",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="monthly",
        units="AFP balances, contribution rates, returns",
        currency="CLP", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
