"""Zillow Research public CSVs (ZORI rents, ZHVI home values).

Endpoint: https://files.zillowstatic.com/research/public_csvs/<family>/<file>.csv
Auth: none.  License: Zillow Research data — free use with attribution
("Zillow Observed Rent Index (ZORI)"), see https://www.zillow.com/research/data/.

series_id: file stem, e.g.
    Metro_zori_uc_sfrcondomfr_sm_month   (ZORI, all homes, smoothed, metro)
    City_zori_uc_sfrcondomfr_sm_month    (ZORI, city)
    Metro_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month (ZHVI)
Wide monthly columns are melted to long (region x date).
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import save_raw

BASE = "https://files.zillowstatic.com/research/public_csvs"
LICENSE = "Zillow Research data (attribution required)"


def fetch(series_id: str = "Metro_zori_uc_sfrcondomfr_sm_month", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    family = "zori" if "zori" in series_id else "zhvi"
    url = f"{BASE}/{family}/{series_id}.csv"
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    save_raw("zillow", series_id, r.content, fetch_ts, "csv")
    wide = pd.read_csv(io.BytesIO(r.content))
    id_cols = [c for c in wide.columns if not c[:2].isdigit()]
    long = wide.melt(id_vars=id_cols, var_name="date", value_name="value").dropna(subset=["value"])
    long["date"] = pd.to_datetime(long["date"])
    long.columns = [c.lower() for c in long.columns]
    path, sha = write_vintage(publisher="zillow", series_id=series_id, frame=long, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="zillow", series_id=series_id, source_url=url,
        methodology_url="https://www.zillow.com/research/methodology-zori-repeat-rent-27092/",
        license=LICENSE, fetch_utc=fetch_ts, rows=len(long), frequency="monthly",
        units="USD per month (ZORI)" if family == "zori" else "USD (ZHVI)", currency="USD",
        start_date=str(long["date"].min().date()), end_date=str(long["date"].max().date()),
        sha256=sha, parquet_path=path,
        extra={"regions": int(long["regionid"].nunique()),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
