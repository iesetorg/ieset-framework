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

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"


def fetch(series_id: str = "pwt_full", *, vintage_utc: datetime | None = None) -> FetchResult:
    path = find_latest("pwt", "xlsx", "xls", "dta")
    fetch_ts = utc_now()
    if path.suffix.lower() == ".dta":
        df = pd.read_stata(path)
    else:
        xls = pd.ExcelFile(path)
        # PWT ships 'Data' + 'Legend' + 'Info' sheets
        sheet = next((s for s in xls.sheet_names if s.lower() == "data"), xls.sheet_names[0])
        df = xls.parse(sheet)

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

    out, sha = write_vintage(publisher="pwt", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="pwt", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://www.rug.nl/ggdc/productivity/pwt/",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="rgdpo/rgdpe (2017 PPP $bn); cn (capital stock); tfp; emp; hc; pop; etc.",
        currency="int_usd_2017_ppp",
        start_date=str(df["year"].min()) if "year" in df.columns and df["year"].notna().any() else None,
        end_date=str(df["year"].max()) if "year" in df.columns and df["year"].notna().any() else None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
