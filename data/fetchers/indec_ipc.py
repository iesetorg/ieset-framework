"""INDEC IPC (Argentine national CPI, base Dec-2016) via apis.datos.gob.ar.

Endpoint: https://apis.datos.gob.ar/series/api/series
Auth: none.  License: CC-BY 4.0 (datos.gob.ar / INDEC).

Pulls the national IPC index components the Milei-disinflation claims argue
about, and derives month-on-month and year-on-year % changes:

    headline   148.3_INIVELNAL_DICI_M_26  Nivel general
    core       148.3_INUCLEONAL_DICI_M_19 Núcleo
    regulated  148.3_IREGULANAL_DICI_M_22 Regulados
    seasonal   148.3_IESTACINAL_DICI_M_25 Estacionales
    goods      147.3_IBIENESNAL_DICI_T_19 Bienes
    services   147.3_ISERVICNAL_DICI_T_22 Servicios

series_id: "all" (default) or one of the keys above, or a raw datos id.
Series starts Dec 2016, so the 2007-2015 falsification window is not covered.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import save_raw

BASE = "https://apis.datos.gob.ar/series/api/series"
LICENSE = "CC-BY 4.0 (Argentina datos.gob.ar / INDEC)"
SERIES = {
    "headline": "148.3_INIVELNAL_DICI_M_26",
    "core": "148.3_INUCLEONAL_DICI_M_19",
    "regulated": "148.3_IREGULANAL_DICI_M_22",
    "seasonal": "148.3_IESTACINAL_DICI_M_25",
    "goods": "147.3_IBIENESNAL_DICI_T_19",
    "services": "147.3_ISERVICNAL_DICI_T_22",
}


def fetch(series_id: str = "all", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    if series_id == "all":
        wanted = SERIES
    elif series_id in SERIES:
        wanted = {series_id: SERIES[series_id]}
    else:
        wanted = {series_id: series_id}
    ids = ",".join(wanted.values())
    r = requests.get(BASE, params={"ids": ids, "format": "json", "limit": 5000}, timeout=90)
    r.raise_for_status()
    save_raw("indec_ipc", series_id, r.content, fetch_ts, "json")
    js = r.json()
    names = list(wanted.keys())
    df = pd.DataFrame(js["data"], columns=["date", *names])
    df["date"] = pd.to_datetime(df["date"])
    long = df.melt(id_vars="date", var_name="component", value_name="index").dropna()
    long = long.sort_values(["component", "date"]).reset_index(drop=True)
    g = long.groupby("component")["index"]
    long["mom_pct"] = g.pct_change() * 100
    long["yoy_pct"] = g.pct_change(12) * 100
    long["country_iso3"] = "ARG"
    path, sha = write_vintage(publisher="indec_ipc", series_id=series_id, frame=long, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="indec_ipc",
        series_id=series_id,
        source_url=f"{BASE}?ids={ids}",
        methodology_url="https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-5-31",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(long),
        frequency="monthly",
        units="index Dec-2016=100; mom_pct/yoy_pct derived",
        currency=None,
        start_date=str(long["date"].min().date()),
        end_date=str(long["date"].max().date()),
        sha256=sha,
        parquet_path=path,
        extra={"components": wanted, "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
