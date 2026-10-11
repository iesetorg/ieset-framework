"""IMF World Economic Outlook via the IMF SDMX 3.0 API (vintage-aware).

Endpoint: https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/<FLOW>/+/<KEY>
Auth: none (verified keyless 2026-10-09).
License: IMF standard terms (attribution required).

Why a second WEO fetcher? data.fetchers.imf_weo uses the DataMapper API, which
only serves the *current* WEO and does not say which release it is. The SDMX
API exposes the live flow ``WEO`` plus frozen release flows such as
``WEO_2025_OCT_VINTAGE`` and ``WEO_2026_APR_VINTAGE``. This fetcher records the
release in every vintage so re-runs after the October 2026 WEO can be diffed
against the April 2026 numbers instead of silently replacing them.

series_id: WEO indicator code, e.g. NGDP_RPCH, PCPIPCH, GGXWDG_NGDP, LUR.
countries: ISO3 list (default: all).
flow:      "WEO" (live), or an explicit vintage flow id, or "latest_vintage".
"""
from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._rawstore import save_raw

BASE = "https://api.imf.org/external/sdmx"
LICENSE = "IMF standard terms (attribution required)"
_VINTAGE_RE = re.compile(r'id="(WEO_(\d{4})_(APR|OCT)_VINTAGE)"')


class ImfWeoSdmxError(RuntimeError):
    pass


def list_vintages() -> list[str]:
    r = requests.get(f"{BASE}/2.1/dataflow", timeout=90)
    r.raise_for_status()
    found = {(int(y), 0 if m == "APR" else 1, fid) for fid, y, m in _VINTAGE_RE.findall(r.text)}
    return [fid for _, _, fid in sorted(found)]


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: list[str] | None = None,
    flow: str = "WEO",
) -> FetchResult:
    fetch_ts = utc_now()
    vintages = list_vintages()
    if flow == "latest_vintage":
        if not vintages:
            raise ImfWeoSdmxError("no WEO_*_VINTAGE dataflows listed")
        flow = vintages[-1]
    ctry = "+".join(countries) if countries else "*"
    url = f"{BASE}/3.0/data/dataflow/IMF.RES/{flow}/%2B/{ctry}.{series_id}.A"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=120)
    if r.status_code == 404:
        raise ImfWeoSdmxError(f"{flow}/{series_id}: no data (404)")
    r.raise_for_status()
    save_raw("imf_weo_sdmx", f"{flow}_{series_id}_{ctry[:40]}", r.content, fetch_ts, "json")
    payload = r.json()["data"]
    struct = payload["structures"][0]
    sdims = struct["dimensions"]["series"]
    odims = struct["dimensions"]["observation"]
    time_vals = [v.get("value") or v.get("id") for v in odims[0]["values"]]
    attrs_series = (struct.get("attributes") or {}).get("series") or []
    recs = []
    for ds in payload["dataSets"]:
        for skey, s in (ds.get("series") or {}).items():
            idx = [int(i) for i in skey.split(":")]
            labels = {d["id"]: d["values"][i]["id"] for d, i in zip(sdims, idx)}
            iso3 = labels.get("COUNTRY") or labels.get("REF_AREA")
            for oi, ov in (s.get("observations") or {}).items():
                val = pd.to_numeric(ov[0], errors="coerce")
                recs.append({"country_iso3": iso3, "year": int(str(time_vals[int(oi)])[:4]), "value": val})
    if not recs:
        raise ImfWeoSdmxError(f"{flow}/{series_id}: empty dataset")
    df = pd.DataFrame(recs).dropna(subset=["value"]).sort_values(["country_iso3", "year"]).reset_index(drop=True)
    df["weo_flow"] = flow
    path, sha = write_vintage(publisher="imf_weo_sdmx", series_id=f"{flow}__{series_id}", frame=df, fetch_utc=fetch_ts)
    oct26 = "WEO_2026_OCT_VINTAGE" in vintages
    return FetchResult(
        publisher="imf_weo_sdmx",
        series_id=f"{flow}__{series_id}",
        source_url=url,
        methodology_url="https://www.imf.org/en/Publications/WEO",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="per WEO indicator definition",
        currency=None,
        start_date=str(df["year"].min()),
        end_date=str(df["year"].max()),
        sha256=sha,
        parquet_path=path,
        extra={
            "weo_flow": flow,
            "available_vintage_flows": vintages,
            "oct_2026_release_published": oct26,
            "note": "Projection years included; filter year<=last actual before testing.",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
