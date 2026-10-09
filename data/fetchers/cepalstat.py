"""CEPALSTAT (UN ECLAC) indicator API.

Endpoint: https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/<id>/data?lang=en&format=json
Auth: none.  License: ECLAC/CEPALSTAT terms (free reuse with attribution).

series_id: CEPALSTAT indicator id, e.g.
    3328  Population in extreme poverty and poverty, by area (%)
    2204  GDP at constant prices, annual growth (%)
Dimension member ids are resolved to names via the response's own
``dimensions`` block; country names map to ISO3 via the ``iso3`` field when
present. Columns: one per dimension (name), value, source_id, notes_ids.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import save_raw

BASE = "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator"
LICENSE = "ECLAC CEPALSTAT (attribution required)"


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    url = f"{BASE}/{series_id}/data"
    r = requests.get(url, params={"lang": "en", "format": "json"}, timeout=180)
    r.raise_for_status()
    save_raw("cepalstat", f"indicator_{series_id}", r.content, fetch_ts, "json")
    body = r.json()["body"]
    dim_names, member = {}, {}
    for d in body["dimensions"]:
        nm = d["name"].split("__")[0].lower().replace(" ", "_")
        dim_names[f"dim_{d['id']}"] = nm
        for m in d["members"]:
            member[m["id"]] = m["name"]
    recs = []
    for row in body["data"]:
        rec = {"value": pd.to_numeric(row.get("value"), errors="coerce"), "iso3": row.get("iso3"),
               "source_id": row.get("source_id"), "notes_ids": row.get("notes_ids")}
        for k, v in row.items():
            if k.startswith("dim_"):
                rec[dim_names.get(k, k)] = member.get(v, v)
        recs.append(rec)
    df = pd.DataFrame(recs)
    year_col = next((c for c in df.columns if c in ("years", "year")), None)
    if year_col:
        df["year"] = pd.to_numeric(df[year_col], errors="coerce")
    meta = body.get("metadata", {})
    path, sha = write_vintage(publisher="cepalstat", series_id=f"indicator_{series_id}", frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="cepalstat", series_id=f"indicator_{series_id}", source_url=f"{url}?lang=en&format=json",
        methodology_url=f"https://statistics.cepal.org/portal/cepalstat/dashboard.html?indicator_id={series_id}&lang=en",
        license=LICENSE, fetch_utc=fetch_ts, rows=len(df), frequency="annual",
        units=meta.get("unit") or "", currency=None,
        start_date=str(int(df["year"].min())) if year_col else None,
        end_date=str(int(df["year"].max())) if year_col else None,
        sha256=sha, parquet_path=path,
        extra={"indicator_name": meta.get("indicator_name"), "dimensions": list(dim_names.values()),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
