"""INSEE BDM (Banque de données macro-économiques) via the keyless SDMX service.

Endpoint: https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/<idbank>[+<idbank>...]
Auth: none (the old api.insee.fr BDM keys were retired 10 Sep 2025; this
public SDMX endpoint needs no key).  License: Licence Ouverte / Etalab 2.0.

series_id: one idbank or several joined with '+', e.g.
    001759970  CPI, all households, France, base 2015 (monthly)
    001688527  ILO unemployment rate, France excl. Mayotte (quarterly)
    010565692  GDP volume, chained (quarterly)
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import save_raw

BASE = "https://bdm.insee.fr/series/sdmx/data/SERIES_BDM"
LICENSE = "Licence Ouverte / Etalab 2.0"


def _period(p: str) -> pd.Timestamp:
    if "-Q" in p:
        y, q = p.split("-Q")
        return pd.Timestamp(int(y), 3 * int(q) - 2, 1)
    if len(p) == 4:
        return pd.Timestamp(int(p), 1, 1)
    return pd.Timestamp(p + "-01") if len(p) == 7 else pd.Timestamp(p)


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    url = f"{BASE}/{series_id}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    save_raw("insee_bdm", series_id, r.content, fetch_ts, "xml")
    root = ET.fromstring(r.content)
    recs, titles = [], {}
    for s in root.iter():
        if not s.tag.endswith("Series"):
            continue
        idb = s.attrib.get("IDBANK")
        titles[idb] = s.attrib.get("TITLE_EN") or s.attrib.get("TITLE_FR")
        for o in s:
            if o.tag.endswith("Obs"):
                v = pd.to_numeric(o.attrib.get("OBS_VALUE"), errors="coerce")
                recs.append({"idbank": idb, "period": o.attrib["TIME_PERIOD"], "date": _period(o.attrib["TIME_PERIOD"]),
                             "value": v, "freq": s.attrib.get("FREQ"), "unit": s.attrib.get("UNIT_MEASURE")})
    df = pd.DataFrame(recs).dropna(subset=["value"]).sort_values(["idbank", "date"]).reset_index(drop=True)
    df["country_iso3"] = "FRA"
    path, sha = write_vintage(publisher="insee_bdm", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="insee_bdm", series_id=series_id, source_url=url,
        methodology_url="https://www.insee.fr/en/information/2868055", license=LICENSE,
        fetch_utc=fetch_ts, rows=len(df), frequency=",".join(sorted(df["freq"].dropna().unique())),
        units=",".join(sorted(df["unit"].dropna().astype(str).unique())), currency=None,
        start_date=str(df["date"].min().date()), end_date=str(df["date"].max().date()),
        sha256=sha, parquet_path=path,
        extra={"titles": titles, "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
