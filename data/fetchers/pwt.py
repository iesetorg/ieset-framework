"""Penn World Tables 10.01 — manual-drop fetcher.

Source URL (browser):
    https://www.rug.nl/ggdc/productivity/pwt/
    → "Penn World Table 10.01" Excel download

GGDC Groningen hosts PWT but direct xlsx URLs 404 on automated access
(obfuscated filenames per download session). Drop the xlsx into
data/manual/pwt/.

PWT 10.01 covers 183 countries 1950-2019 with productivity, capital
stocks, TFP decomposition, PPP-adjusted output — gold standard for
cross-country growth accounting.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"
DOWNLOAD_URL = "https://dataverse.nl/api/access/datafile/354095"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}


def _load_frame_from_path(path) -> pd.DataFrame:
    if path.suffix.lower() == ".dta":
        return pd.read_stata(path)
    xls = pd.ExcelFile(path)
    sheet = next((s for s in xls.sheet_names if s.lower() == "data"), xls.sheet_names[0])
    return xls.parse(sheet)


def _load_frame_from_bytes(payload: bytes) -> pd.DataFrame:
    xls = pd.ExcelFile(io.BytesIO(payload))
    sheet = next((s for s in xls.sheet_names if s.lower() == "data"), xls.sheet_names[0])
    return xls.parse(sheet)


# Common PWT column codes that hypotheses reference as pseudo-series.
_PSEUDO_SERIES: set[str] = {
    "rtfpna", "rgdpe", "rgdpo", "rgdpna", "pop", "emp", "avh", "hc",
    "ccon", "cda", "cgdpe", "cgdpo", "cn", "ck", "ctfp", "cwtfp",
    "rconna", "rdana", "rnna", "rkna", "rwtfpna", "labsh", "irr",
    "delta", "xr", "pl_con", "pl_da", "pl_gdpo", "rgdpe_per_capita",
    "rgdpo_pop", "rgdpo_per_emp", "rkna_to_rgdpna", "rkna_per_emp",
    "ccon_pop", "csh_i", "csh_x",
}


def _load_full_frame() -> pd.DataFrame:
    try:
        r = requests.get(DOWNLOAD_URL, headers=UA, timeout=120)
        r.raise_for_status()
        df = _load_frame_from_bytes(r.content)
        source_url = DOWNLOAD_URL
        source_note = "dataverse"
    except Exception:
        path = find_latest("pwt", "xlsx", "xls", "dta")
        df = _load_frame_from_path(path)
        source_url = f"manual://{path.name}"
        source_note = path.name

    # Standardise country code column
    for col in ("countrycode", "isocode"):
        if col in df.columns:
            df = df.rename(columns={col: "country_iso3"})
            break
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    return df, source_url, source_note


def fetch(series_id: str = "pwt_full", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()

    # Pseudo-series: extract a single column from the full dataset.
    if series_id in _PSEUDO_SERIES:
        df_full, source_url, source_note = _load_full_frame()
        col = series_id
        # Handle synthetic per-capita / per-emp / ratio series.
        if col == "rgdpe_per_capita" and col not in df_full.columns:
            df_full[col] = df_full["rgdpe"] / df_full["pop"]
        elif col == "rgdpo_pop" and col not in df_full.columns:
            df_full[col] = df_full["rgdpo"] / df_full["pop"]
        elif col == "rgdpo_per_emp" and col not in df_full.columns:
            df_full[col] = df_full["rgdpo"] / df_full["emp"]
        elif col == "rkna_to_rgdpna" and col not in df_full.columns:
            df_full[col] = df_full["rkna"] / df_full["rgdpna"]
        elif col == "rkna_per_emp" and col not in df_full.columns:
            df_full[col] = df_full["rkna"] / df_full["emp"]
        elif col == "ccon_pop" and col not in df_full.columns:
            df_full[col] = df_full["ccon"] / df_full["pop"]

        if col not in df_full.columns:
            raise KeyError(f"{col} not in PWT columns and no synthetic recipe defined")
        df = df_full[["country_iso3", "country", "year", col]].copy()
        df = df.rename(columns={col: "value"})
        out, sha = write_vintage(publisher="pwt", series_id=series_id, frame=df, fetch_utc=fetch_ts)
        return FetchResult(
            publisher="pwt", series_id=series_id,
            source_url=source_url,
            methodology_url="https://www.rug.nl/ggdc/productivity/pwt/",
            license=LICENSE, fetch_utc=fetch_ts,
            rows=len(df), frequency="annual",
            units=col,
            currency="int_usd_2017_ppp",
            start_date=str(df["year"].min()) if df["year"].notna().any() else None,
            end_date=str(df["year"].max()) if df["year"].notna().any() else None,
            sha256=sha, parquet_path=out,
            extra={"source_note": source_note, "pseudo_series": True,
                   "parent": "pwt_full", "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
        )

    df, source_url, source_note = _load_full_frame()
    out, sha = write_vintage(publisher="pwt", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="pwt", series_id=series_id,
        source_url=source_url,
        methodology_url="https://www.rug.nl/ggdc/productivity/pwt/",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="rgdpo/rgdpe (2017 PPP $bn); cn (capital stock); tfp; emp; hc; pop; etc.",
        currency="int_usd_2017_ppp",
        start_date=str(df["year"].min()) if "year" in df.columns and df["year"].notna().any() else None,
        end_date=str(df["year"].max()) if "year" in df.columns and df["year"].notna().any() else None,
        sha256=sha, parquet_path=out,
        extra={"source_note": source_note, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
