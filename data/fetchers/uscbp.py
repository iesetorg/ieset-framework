"""US Customs and Border Protection — Nationwide Encounters (monthly CSV).

Landing page: https://www.cbp.gov/document/stats/nationwide-encounters
Auth: none.  License: US Government work (public domain).

CBP republishes a rolling multi-FY CSV each month (file name embeds the
latest month, e.g. nationwide-encounters-fy23-fy26-aug-state.csv). The fetcher
scrapes the landing page for the newest file of the requested flavour, archives
the raw CSV, and adds a calendar ``date`` (fiscal year starts in October).

series_id: "state" (default) or "aor" (area of responsibility).
Columns kept: fiscal_year, month_grouping, month, land_border_region, state|aor,
demographic, citizenship, title_of_authority, encounter_count, date.
"""
from __future__ import annotations

import io
import re
from datetime import datetime

import pandas as pd
import requests

from ._base import ROOT, FetchResult, utc_now, write_vintage
from ._rawstore import BROWSER_UA, save_raw

PAGE = "https://www.cbp.gov/document/stats/nationwide-encounters"
LICENSE = "US Government work — public domain"
_MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def _latest_csv(kind: str) -> str:
    html = requests.get(PAGE, headers={"User-Agent": BROWSER_UA}, timeout=60).text
    links = re.findall(r'href="(/sites/default/files/[^"]*nationwide-encounters[^"]*-' + kind + r'(?:_\d+)?\.csv)"', html)
    if not links:
        raise RuntimeError(f"no {kind} CSV link on {PAGE}")
    return "https://www.cbp.gov" + links[0]  # page lists newest first


def fetch(series_id: str = "state", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    url = _latest_csv(series_id)
    r = requests.get(url, headers={"User-Agent": BROWSER_UA}, timeout=120)
    r.raise_for_status()
    raw_path, raw_sha = save_raw("uscbp", url.rsplit("/", 1)[-1], r.content, fetch_ts, "csv")
    df = pd.read_csv(io.BytesIO(r.content))
    df.columns = [re.sub(r"[^a-z0-9]+", "_", c.lower()).strip("_") for c in df.columns]
    df = df.rename(columns={"month_abbv": "month"})
    df["encounter_count"] = pd.to_numeric(df["encounter_count"], errors="coerce")
    mnum = df["month"].str.upper().map(_MONTHS)
    df["fiscal_year_label"] = df["fiscal_year"].astype(str)
    df["fiscal_year"] = df["fiscal_year_label"].str.extract(r"(\d{4})")[0].astype(int)  # "2026 (FYTD)" -> 2026
    cal_year = df["fiscal_year"] - (mnum >= 10).astype(int)
    df["date"] = pd.to_datetime(dict(year=cal_year, month=mnum, day=1))
    path, sha = write_vintage(publisher="uscbp", series_id=f"nationwide_encounters_{series_id}", frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="uscbp", series_id=f"nationwide_encounters_{series_id}", source_url=url,
        methodology_url=PAGE, license=LICENSE, fetch_utc=fetch_ts, rows=len(df), frequency="monthly",
        units="encounters (count)", currency=None,
        start_date=str(df["date"].min().date()), end_date=str(df["date"].max().date()),
        sha256=sha, parquet_path=path,
        extra={"raw_path": str(raw_path.relative_to(ROOT)), "raw_sha256": raw_sha,
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
