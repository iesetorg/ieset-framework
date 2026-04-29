"""
UNODC Crime and Criminal Justice data
https://dataunodc.un.org

series_id options:
  intentional_homicide — annual homicide count + rate by country, sex
  violent_crime        — assault, rape, robbery, kidnapping
  corruption           — bribery statistics
  prisons              — prison population per 100k

publisher_id: unodc
No auth required. CC-BY-3.0-IGO.

Note: UNODC URLs have changed multiple times; if a fetch returns 404 the caller
should check the UNODC data portal at https://dataunodc.un.org/data for current download links.
"""
from __future__ import annotations
import io
import requests
import pandas as pd
from ._base import FetchResult, utc_now, write_vintage

BASE = "https://dataunodc.un.org/sites/dataunodc.un.org/files"
METHODOLOGY = "https://www.unodc.org/unodc/en/data-and-analysis/statistics.html"
LICENSE = "CC-BY-3.0-IGO"

SERIES_MAP = {
    "intentional_homicide": "data_cts_intentional_homicide.xlsx",
    "violent_crime": "data_cts_violent_and_sexual_crime.xlsx",
    "corruption": "data_cts_corruption.xlsx",
    "prisons": "data_cts_prisons.xlsx",
}


def fetch(series_id: str, **kwargs) -> FetchResult:
    if series_id not in SERIES_MAP:
        raise ValueError(
            f"Unknown UNODC series_id '{series_id}'. Use one of: {list(SERIES_MAP)}"
        )
    url = f"{BASE}/{SERIES_MAP[series_id]}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    # UNODC Excel files typically have metadata header rows + data sheet named "data_cts_..."
    df = pd.read_excel(io.BytesIO(r.content), sheet_name=0, skiprows=2)
    # Normalise column names — UNODC uses title-case with spaces
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    # Coerce object cols to str for pyarrow safety
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str)
    # Infer year range
    year_col = next((c for c in df.columns if "year" in c.lower()), None)
    start = str(df[year_col].min()) if year_col and len(df) else ""
    end = str(df[year_col].max()) if year_col and len(df) else ""
    now = utc_now()
    path, digest = write_vintage(
        publisher="unodc",
        series_id=series_id,
        frame=df,
        fetch_utc=now,
    )
    return FetchResult(
        publisher="unodc",
        series_id=series_id,
        source_url=url,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=now,
        rows=len(df),
        frequency="A",
        units="persons",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=digest,
        parquet_path=path,
    )
