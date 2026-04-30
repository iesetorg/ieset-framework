"""Mercatus QuantGov RegData — US federal regulatory restrictiveness.

Tracks the volume and industry-distribution of federal regulation using the
RegData word-count methodology (occurrences of binding-language verbs:
"shall", "must", "may not", "required", "prohibited" in the Code of Federal
Regulations) plus the Federal Register annual page count (1936-present).

Published by the Mercatus Center / QuantGov project at George Mason University.
Project page: https://www.quantgov.org/regdata-us

Data access notes
-----------------
QuantGov publishes annual snapshot CSVs but does not advertise stable direct
URLs on a documentation page; the project distributes data via per-release
download links from the landing page. We therefore probe a list of known
candidate URLs (newest snapshot first) and use whichever responds with a
parseable CSV. If none respond, the fetcher raises and the caller should fall
back to a manual drop in `data/manual/mercatus/<series_id>.csv`.

Known URL patterns (subject to QuantGov maintenance):
  - https://www.quantgov.org/static/regdata-us/regdata_us_<version>_annual.csv
  - https://quantgov.org/wp-content/uploads/regdata_us_<version>.csv
  - https://github.com/QuantGov/regdata-us/raw/main/data/regdata_us_annual.csv

Series supported (small registry; extend as QuantGov publishes new vintages):
  regdata_us_federal_total            — federal binding-word count, all CFR
  regdata_us_federal_register_pages   — Federal Register total pages per year
  regdata_us_finance_naics52          — NAICS 52 (Finance & Insurance)
  regdata_us_manufacturing_naics31    — NAICS 31-33 (Manufacturing)
  regdata_us_health_naics62           — NAICS 62 (Health Care & Social Asst.)

License: open-data (Mercatus QuantGov terms; non-commercial reuse with
citation). Schema enum doesn't include "open_data", so we tag as "unknown".
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from ._base import FetchResult, ROOT, utc_now, write_vintage

PUBLISHER = "mercatus"
LICENSE = "unknown"  # treat per schema enum; actual is open-data with citation
METHODOLOGY = "https://www.quantgov.org/regdata-us"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15"}

# Series registry: each entry maps a logical series id to one or more candidate
# CSV URLs and the column we treat as the value for that series.
# `naics_filter` selects a subset of an industry-keyed CSV; None = all rows.
SUPPORTED: dict[str, dict] = {
    "regdata_us_federal_total": {
        "urls": [
            "https://www.quantgov.org/static/regdata-us/regdata_us_5_0_annual.csv",
            "https://quantgov.org/wp-content/uploads/regdata_us_5_0_annual.csv",
            "https://github.com/QuantGov/regdata-us/raw/main/data/regdata_us_annual.csv",
        ],
        "value_col": "restrictions",
        "naics_filter": None,
        "frequency": "annual",
        "units": "binding-language word count (CFR)",
        "desc": "US federal regulatory restrictions, total (RegData v5)",
    },
    "regdata_us_federal_register_pages": {
        "urls": [
            "https://www.quantgov.org/static/regdata-us/federal_register_pages.csv",
            "https://quantgov.org/wp-content/uploads/federal_register_pages.csv",
            "https://github.com/QuantGov/regdata-us/raw/main/data/federal_register_pages.csv",
        ],
        "value_col": "pages",
        "naics_filter": None,
        "frequency": "annual",
        "units": "Federal Register pages",
        "desc": "US Federal Register total pages, 1936-present",
    },
    "regdata_us_finance_naics52": {
        "urls": [
            "https://www.quantgov.org/static/regdata-us/regdata_us_5_0_industry.csv",
            "https://quantgov.org/wp-content/uploads/regdata_us_5_0_industry.csv",
            "https://github.com/QuantGov/regdata-us/raw/main/data/regdata_us_industry.csv",
        ],
        "value_col": "restrictions",
        "naics_filter": "52",
        "frequency": "annual",
        "units": "binding-language word count (CFR), NAICS-weighted",
        "desc": "US federal restrictions targeting NAICS 52 Finance & Insurance",
    },
    "regdata_us_manufacturing_naics31": {
        "urls": [
            "https://www.quantgov.org/static/regdata-us/regdata_us_5_0_industry.csv",
            "https://quantgov.org/wp-content/uploads/regdata_us_5_0_industry.csv",
            "https://github.com/QuantGov/regdata-us/raw/main/data/regdata_us_industry.csv",
        ],
        "value_col": "restrictions",
        "naics_filter": "31",  # also matches 32/33 via prefix-match in loader
        "frequency": "annual",
        "units": "binding-language word count (CFR), NAICS-weighted",
        "desc": "US federal restrictions targeting NAICS 31-33 Manufacturing",
    },
    "regdata_us_health_naics62": {
        "urls": [
            "https://www.quantgov.org/static/regdata-us/regdata_us_5_0_industry.csv",
            "https://quantgov.org/wp-content/uploads/regdata_us_5_0_industry.csv",
            "https://github.com/QuantGov/regdata-us/raw/main/data/regdata_us_industry.csv",
        ],
        "value_col": "restrictions",
        "naics_filter": "62",
        "frequency": "annual",
        "units": "binding-language word count (CFR), NAICS-weighted",
        "desc": "US federal restrictions targeting NAICS 62 Health Care",
    },
}


class MercatusError(RuntimeError):
    pass


def _try_download(urls: list[str]) -> tuple[bytes, str]:
    last_exc: Exception | None = None
    for url in urls:
        try:
            r = requests.get(url, headers=UA, timeout=60, allow_redirects=True)
        except requests.RequestException as e:
            last_exc = e
            continue
        if r.status_code == 200 and r.content and len(r.content) > 200:
            ctype = r.headers.get("content-type", "").lower()
            # Accept text/csv, text/plain, octet-stream; reject HTML error pages.
            head = r.content[:512].lstrip().lower()
            if head.startswith(b"<!doctype") or head.startswith(b"<html"):
                last_exc = MercatusError(f"HTML response (likely 404 page) at {url}")
                continue
            if "csv" in ctype or "plain" in ctype or "octet" in ctype or b"," in head:
                return r.content, url
        last_exc = MercatusError(f"HTTP {r.status_code} at {url}")
    raise MercatusError(f"all candidate URLs failed; last={last_exc}")


def _load_manual_fallback(series_id: str) -> tuple[bytes, str] | None:
    """Manual-drop fallback. Place CSV at data/manual/mercatus/<series_id>.csv."""
    p = ROOT / "data" / "manual" / "mercatus" / f"{series_id}.csv"
    if p.exists():
        return p.read_bytes(), f"manual://{p.relative_to(ROOT)}"
    return None


def _filter_naics(df: pd.DataFrame, naics_prefix: str) -> pd.DataFrame:
    """Filter an industry-keyed RegData frame to NAICS rows matching a prefix.

    QuantGov industry CSVs typically carry an `industry` or `naics` column with
    2-6 digit codes. We match by string prefix so '31' picks up 31-33 mfg.
    """
    naics_col = next(
        (c for c in df.columns if c.lower() in ("naics", "industry", "industry_code", "naics_code")),
        None,
    )
    if naics_col is None:
        return df  # nothing to filter on; leave the frame intact
    s = df[naics_col].astype("string").str.strip()
    return df[s.str.startswith(naics_prefix, na=False)].copy()


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    if series_id not in SUPPORTED:
        raise MercatusError(
            f"unknown Mercatus series_id {series_id!r}; supported: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    fetch_ts = utc_now()

    # 1. Try live URLs; 2. fall back to manual drop.
    try:
        content, source_url = _try_download(spec["urls"])
    except MercatusError:
        manual = _load_manual_fallback(series_id)
        if manual is None:
            raise
        content, source_url = manual

    df = pd.read_csv(io.BytesIO(content))
    df.columns = [str(c).strip().lower() for c in df.columns]

    if spec["naics_filter"]:
        df = _filter_naics(df, spec["naics_filter"])

    # Normalise year column
    year_col = next((c for c in df.columns if c in ("year", "yr", "date")), None)
    if year_col and year_col != "year":
        df = df.rename(columns={year_col: "year"})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    # Normalise value column
    val = spec["value_col"]
    if val not in df.columns:
        # heuristic: pick first numeric non-year column
        numeric_cols = [c for c in df.columns if c != "year" and pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            df = df.rename(columns={numeric_cols[0]: val})

    if val in df.columns:
        df[val] = pd.to_numeric(df[val], errors="coerce")

    if "year" in df.columns:
        df = df.dropna(subset=["year"]).sort_values("year").reset_index(drop=True)

    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = str(int(df["year"].min())) if "year" in df.columns and len(df) else None
    end = str(int(df["year"].max())) if "year" in df.columns and len(df) else None

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=source_url,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec["frequency"],
        units=spec["units"],
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "naics_filter": spec["naics_filter"],
            "value_col": spec["value_col"],
            "columns": list(df.columns),
            "description": spec["desc"],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
