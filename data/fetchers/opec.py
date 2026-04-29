"""OPEC Annual Statistical Bulletin — manual-drop fetcher.

Source URL (browser):
    https://asb.opec.org/ → "Download ASB Interactive" / Excel

OPEC's CDN blocks automated access across all configs tried (plain 403,
Zenrows returns HTML-instead-of-xlsx). ASB ships as a multi-sheet xlsx
with per-topic tables (production, exports, reserves, revenues, etc.).

series_id picks the topic; defaults to the whole workbook's
consolidated country-year production panel. Detailed sheet names can be
queried via the ASB table of contents.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"


def fetch(series_id: str = "asb_full", *, vintage_utc: datetime | None = None, sheet: str | None = None) -> FetchResult:
    path = find_latest("opec", "xlsx", "xls")
    fetch_ts = utc_now()
    xls = pd.ExcelFile(path)
    # User-specified sheet takes precedence; else union of all sheets tagged
    if sheet is not None:
        if sheet not in xls.sheet_names:
            raise RuntimeError(f"sheet {sheet!r} not in {path.name}; sheets: {xls.sheet_names[:20]}")
        df = xls.parse(sheet)
        for c in df.columns:
            if df[c].dtype == "object":
                df[c] = df[c].astype("string")
        target = sheet
    else:
        frames = []
        for s in xls.sheet_names:
            try:
                d = xls.parse(s)
                d["__sheet"] = s
                frames.append(d)
            except Exception:
                continue
        df = pd.concat(frames, ignore_index=True)
        for c in df.columns:
            if df[c].dtype == "object":
                df[c] = df[c].astype("string")
        target = "(all sheets concatenated)"

    out, sha = write_vintage(publisher="opec", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="opec", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.opec.org/opec_web/en/publications/202.htm",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="mixed per sheet (crude production mbbl/d, revenues USDbn, reserves, etc.)",
        currency=None, start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "target_sheet": target, "n_sheets": len(xls.sheet_names),
               "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
