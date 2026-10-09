"""US EIA Open Data API v2 (live; complements the seed-only data.fetchers.eia).

Endpoint: https://api.eia.gov/v2/<route>/data/
Auth: EIA_API_KEY (env or the gitignored repo .env). Key is never written to
vintages, manifests or raw files (raw payloads are stored without the URL).
License: US Government work (public domain).

series_id: route, e.g.
    electricity/retail-sales      (price cents/kWh, sales, revenue by state/sector)
    natural-gas/pri/sum           (natural gas prices)
    petroleum/pri/gnd             (retail gasoline/diesel)
kwargs: frequency ("monthly"/"annual"), data (list of columns, default ["price"]),
        facets (dict facet -> list), start/end (YYYY or YYYY-MM).
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import load_env_file, save_raw

BASE = "https://api.eia.gov/v2"
LICENSE = "US Government work — public domain"


def fetch(series_id: str = "electricity/retail-sales", *, vintage_utc: datetime | None = None,
          frequency: str = "annual", data: list[str] | None = None, facets: dict | None = None,
          start: str | None = None, end: str | None = None) -> FetchResult:
    load_env_file()
    key = os.environ.get("EIA_API_KEY")
    if not key:
        raise RuntimeError("EIA_API_KEY not set (env or repo .env)")
    fetch_ts = utc_now()
    data = data or ["price"]
    params: list[tuple[str, str]] = [("frequency", frequency)]
    params += [(f"data[{i}]", c) for i, c in enumerate(data)]
    for f, vals in (facets or {}).items():
        params += [(f"facets[{f}][]", v) for v in vals]
    if start:
        params.append(("start", start))
    if end:
        params.append(("end", end))
    params += [("sort[0][column]", "period"), ("sort[0][direction]", "asc"), ("length", "5000")]
    rows, offset, pages = [], 0, []
    while True:
        r = requests.get(f"{BASE}/{series_id}/data/", params=params + [("offset", str(offset)), ("api_key", key)], timeout=120)
        r.raise_for_status()
        resp = r.json()["response"]
        pages.append(resp)
        chunk = resp.get("data") or []
        rows.extend(chunk)
        total = int(resp.get("total") or 0)
        offset += len(chunk)
        if not chunk or offset >= total or offset >= 200000:
            break
    save_raw("eia_v2", series_id.replace("/", "_"), json.dumps({"params": params, "pages": pages}).encode(), fetch_ts, "json")
    df = pd.DataFrame(rows)
    for c in data:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    name = series_id.replace("/", "_") + f"_{frequency}"
    if facets:
        name += "_" + "_".join(f"{k}-{'-'.join(v)}" for k, v in sorted(facets.items()))
    path, sha = write_vintage(publisher="eia_v2", series_id=name, frame=df, fetch_utc=fetch_ts)
    units = ",".join(sorted({str(v) for c in data for v in df.get(f"{c}-units", pd.Series(dtype=str)).dropna().unique()}))
    return FetchResult(
        publisher="eia_v2", series_id=name, source_url=f"{BASE}/{series_id}/data/ (api_key redacted)",
        methodology_url=f"https://www.eia.gov/opendata/browser/{series_id}", license=LICENSE,
        fetch_utc=fetch_ts, rows=len(df), frequency=frequency, units=units, currency="USD",
        start_date=str(df["period"].min()) if len(df) else None, end_date=str(df["period"].max()) if len(df) else None,
        sha256=sha, parquet_path=path,
        extra={"facets": facets or {}, "data_cols": data,
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
