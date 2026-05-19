"""WIPO IP statistics fetcher.

Primary WIPO IP Statistics Data Center downloads are browser-oriented. For the
core country-year patent application measures that IESET specs need, the World
Bank WDI API republishes WIPO-sourced series with stable machine-readable
indicator IDs:

  - IP.PAT.RESD   Patent applications, residents
  - IP.PAT.NRES   Patent applications, nonresidents

The emitted publisher is still ``wipo`` because the statistical source is WIPO;
the manifest explicitly records the World Bank API as the transport mirror.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Iterable

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as robust_get

WB_BASE = "https://api.worldbank.org/v2"
LICENSE = "WIPO Statistics Database terms; World Bank API transport"
METHODOLOGY_URL = "https://www.wipo.int/en/web/ip-statistics/about"

_SERIES_MAP: dict[str, str] = {
    "patent_applications_resident": "IP.PAT.RESD",
    "patent_applications_residents": "IP.PAT.RESD",
    "patent_applications_non_resident": "IP.PAT.NRES",
    "patent_applications_nonresident": "IP.PAT.NRES",
}

_COMBINED_SERIES = {
    "patent_applications",
    "ip_statistics_data_center",
}


class WipoError(RuntimeError):
    pass


def _iter_wb_pages(indicator: str, countries: str) -> Iterable[dict[str, Any]]:
    page = 1
    while True:
        payload = robust_get(
            f"{WB_BASE}/country/{countries}/indicator/{indicator}",
            params={"format": "json", "per_page": "20000", "page": str(page)},
            timeout=180,
        )
        data = json.loads(payload.text)
        if not isinstance(data, list) or len(data) < 2:
            raise WipoError(f"World Bank mirror error for {indicator}: {data}")
        meta, rows = data
        if not rows:
            return
        for row in rows:
            yield row
        if page >= int(meta.get("pages", 1)):
            return
        page += 1


def _fetch_indicator_frame(indicator: str, countries: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows = list(_iter_wb_pages(indicator, countries))
    if not rows:
        raise WipoError(f"WIPO/WB mirror returned no rows for {indicator}")
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
    df["country_iso3"] = df["countryiso3code"]
    df["country_name"] = df["country"].apply(lambda c: c.get("value") if isinstance(c, dict) else None)
    df["indicator_id"] = df["indicator"].apply(lambda i: i.get("id") if isinstance(i, dict) else indicator)
    df["indicator_name"] = df["indicator"].apply(lambda i: i.get("value") if isinstance(i, dict) else None)
    df = (
        df[["country_iso3", "country_name", "indicator_id", "indicator_name", "year", "value", "unit", "obs_status", "decimal"]]
        .dropna(subset=["country_iso3", "year"])
        .sort_values(["country_iso3", "year"])
        .reset_index(drop=True)
    )
    meta_payload = robust_get(
        f"{WB_BASE}/indicator/{indicator}",
        params={"format": "json"},
        timeout=60,
    )
    meta_json = json.loads(meta_payload.text)
    meta = meta_json[1][0] if isinstance(meta_json, list) and len(meta_json) > 1 and meta_json[1] else {}
    return df, meta


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: str = "all",
) -> FetchResult:
    fetch_ts = utc_now()
    requested = series_id

    if series_id == "patent_citations":
        raise WipoError(
            "WIPO patent_citations is not exposed through the public WDI mirror; "
            "use PATSTAT/Dimensions/PatentsView or a manual WIPO/Patstat extract."
        )

    if series_id in _COMBINED_SERIES:
        resident, resident_meta = _fetch_indicator_frame("IP.PAT.RESD", countries)
        nonresident, nonresident_meta = _fetch_indicator_frame("IP.PAT.NRES", countries)
        df = pd.concat([resident, nonresident], ignore_index=True)
        wide = (
            df.pivot_table(
                index=["country_iso3", "country_name", "year"],
                columns="indicator_id",
                values="value",
                aggfunc="first",
            )
            .reset_index()
            .rename_axis(None, axis=1)
        )
        if "IP.PAT.RESD" in wide.columns and "IP.PAT.NRES" in wide.columns:
            wide["value"] = wide[["IP.PAT.RESD", "IP.PAT.NRES"]].sum(axis=1, min_count=1)
        else:
            wide["value"] = pd.NA
        wide["indicator_id"] = requested
        wide["indicator_name"] = "Patent applications, resident plus non-resident filings"
        df = wide.sort_values(["country_iso3", "year"]).reset_index(drop=True)
        source_note = "; ".join(
            n
            for n in (
                resident_meta.get("sourceNote"),
                nonresident_meta.get("sourceNote"),
            )
            if n
        )
        units = "applications"
    elif series_id in _SERIES_MAP:
        indicator = _SERIES_MAP[series_id]
        df, meta = _fetch_indicator_frame(indicator, countries)
        source_note = meta.get("sourceNote") or ""
        units = meta.get("unit") or "applications"
    else:
        raise WipoError(
            f"unsupported WIPO series_id {series_id!r}; "
            f"known: {sorted(set(_SERIES_MAP) | _COMBINED_SERIES | {'patent_citations'})}"
        )

    path, sha = write_vintage(
        publisher="wipo",
        series_id=requested,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="wipo",
        series_id=requested,
        source_url=f"{WB_BASE}/country/{countries}/indicator/{_SERIES_MAP.get(series_id, 'IP.PAT.RESD;IP.PAT.NRES')}?format=json",
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(df["year"].min())) if len(df) and "year" in df.columns else None,
        end_date=str(int(df["year"].max())) if len(df) and "year" in df.columns else None,
        sha256=sha,
        parquet_path=path,
        extra={
            "transport": "world_bank_wdi_mirror",
            "wipo_source": "WIPO Statistics Database",
            "source_note": source_note[:800],
            "countries_param": countries,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
