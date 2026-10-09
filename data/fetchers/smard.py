"""SMARD (Bundesnetzagentur) German electricity market data — chart_data API.

Endpoint: https://www.smard.de/app/chart_data/<filter>/<region>/index_<res>.json
          https://www.smard.de/app/chart_data/<filter>/<region>/<filter>_<region>_<res>_<ts>.json
Auth: none.  License: CC BY 4.0 (Bundesnetzagentur | SMARD.de).

series_id: a filter name below or a numeric SMARD filter id.
region:    "DE" (default), "DE-LU", "AT", ...
resolution: "month" (default), "week", "day", "hour", "quarterhour".

Filters (MWh unless noted):
    price_de_lu 4169 (EUR/MWh day-ahead)  load 410
    lignite 1223  nuclear 1224  wind_offshore 1225  hydro 1226
    other_conventional 1227  other_renewable 1228  biomass 4066
    wind_onshore 4067  solar 4068  hard_coal 4069  pumped_storage 4070  gas 4071
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://www.smard.de/app/chart_data"
LICENSE = "CC BY 4.0 (Bundesnetzagentur | SMARD.de)"
FILTERS = {
    "price_de_lu": 4169, "load": 410, "lignite": 1223, "nuclear": 1224, "wind_offshore": 1225,
    "hydro": 1226, "other_conventional": 1227, "other_renewable": 1228, "biomass": 4066,
    "wind_onshore": 4067, "solar": 4068, "hard_coal": 4069, "pumped_storage": 4070, "gas": 4071,
}


def fetch(series_id: str = "price_de_lu", *, vintage_utc: datetime | None = None,
          region: str = "DE", resolution: str = "month") -> FetchResult:
    fetch_ts = utc_now()
    fid = FILTERS.get(series_id, None) or int(series_id)
    idx = requests.get(f"{BASE}/{fid}/{region}/index_{resolution}.json", timeout=60)
    idx.raise_for_status()
    stamps = idx.json()["timestamps"]
    rows = []
    for ts in stamps:
        r = requests.get(f"{BASE}/{fid}/{region}/{fid}_{region}_{resolution}_{ts}.json", timeout=60)
        r.raise_for_status()
        rows.extend(r.json().get("series") or [])
    df = pd.DataFrame(rows, columns=["ts_ms", "value"]).dropna().drop_duplicates("ts_ms")
    df["date"] = pd.to_datetime(df["ts_ms"], unit="ms", utc=True).dt.tz_convert("Europe/Berlin").dt.tz_localize(None)
    df = df.drop(columns="ts_ms").sort_values("date").reset_index(drop=True)
    df["filter_id"] = fid
    df["region"] = region
    name = f"{series_id}_{region}_{resolution}"
    path, sha = write_vintage(publisher="smard", series_id=name, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="smard", series_id=name,
        source_url=f"{BASE}/{fid}/{region}/index_{resolution}.json",
        methodology_url="https://www.smard.de/en/user-guide",
        license=LICENSE, fetch_utc=fetch_ts, rows=len(df), frequency=resolution,
        units="EUR/MWh" if fid == 4169 else "MWh",
        currency="EUR" if fid == 4169 else None,
        start_date=str(df["date"].min().date()), end_date=str(df["date"].max().date()),
        sha256=sha, parquet_path=path,
        extra={"filter_id": fid, "chunks": len(stamps),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
