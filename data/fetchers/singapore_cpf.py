"""Singapore Central Provident Fund — manual-drop fetcher.

Source URL (browser):
    https://www.cpf.gov.sg/member/infohub/reports-and-statistics/cpf-statistics

CPF publishes annual statistics xlsx with member balances, contribution
rates, sector breakdowns, Ordinary/Special/MediSave/Retirement Account
allocations. Essential for welfare-architecture hypothesis (Nordic vs
forced-saving comparison per D.1.5).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "unknown"


def fetch(series_id: str = "cpf_statistics_annual", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("singapore_cpf", "xlsx", "xls", "csv")
    fetch_ts = utc_now()
    xls = pd.ExcelFile(path)
    sheet = next((s for s in xls.sheet_names if any(k in s.lower() for k in ("members", "balance", "summary", "total", "data"))), xls.sheet_names[0])
    df = xls.parse(sheet)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    out, sha = write_vintage(publisher="singapore_cpf", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="singapore_cpf", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.cpf.gov.sg/member/infohub/reports-and-statistics",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="per table (SGD, member counts, %)",
        currency="SGD", start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "sheet": sheet, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
