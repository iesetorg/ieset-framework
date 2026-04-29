"""Bank of England Interactive Statistical Database (IADB) fetcher.

Endpoint: https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp
Auth: none (but CDN requires a browser-shaped User-Agent).
License: UK Open Government Licence v3.0.

Series codes are BoE's internal identifiers (e.g. 'LPMAUYM' = M4 monetary
stock, monthly, amounts outstanding).
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp"
LICENSE = "ogl_uk_3_0"
# Required to pass BoE's Akamai UA-check.
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"}


class BoeError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    date_from: str = "01/Jan/1963",
    date_to: str = "now",
) -> FetchResult:
    """series_id: BoE IADB series code (uppercase letters + digits).
    date_from / date_to in 'dd/Mmm/yyyy' format as BoE's IADB expects.
    """
    fetch_ts = utc_now()
    params = {
        "csv.x": "yes",
        "Datefrom": date_from,
        "Dateto": date_to,
        "SeriesCodes": series_id,
        "CSVF": "TN",
        "UsingCodes": "Y",
        "VPD": "Y",
        "VFD": "N",
    }
    r = requests.get(BASE, params=params, headers=UA, timeout=60)
    r.raise_for_status()
    text = r.text
    if not text.startswith("DATE") and "DATE," not in text[:200]:
        raise BoeError(f"BoE {series_id}: unexpected payload (first 150 chars): {text[:150]!r}")
    df = pd.read_csv(io.StringIO(text))
    # Standard BoE CSV shape: 'DATE,<SERIES_CODE>'
    if "DATE" in df.columns:
        df = df.rename(columns={"DATE": "date"})
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    if series_id in df.columns:
        df = df.rename(columns={series_id: "value"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="boe",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="boe",
        series_id=series_id,
        source_url=f"{BASE}?SeriesCodes={series_id}&Datefrom={date_from}&Dateto={date_to}&CSVF=TN&UsingCodes=Y",
        methodology_url=f"https://www.bankofengland.co.uk/boeapps/iadb/index.asp?Travel=NIxSTxTSx&levels=2&FullSeries=1&SeriesCodes={series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="per series",
        units="per series metadata",
        currency="GBP",
        start_date=str(df["date"].min().date()) if "date" in df.columns and df["date"].notna().any() else None,
        end_date=str(df["date"].max().date()) if "date" in df.columns and df["date"].notna().any() else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "date_from": date_from,
            "date_to": date_to,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
