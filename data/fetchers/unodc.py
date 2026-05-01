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


def _normalise_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str)
    return df


def _looks_like_unodc_data(df: pd.DataFrame) -> bool:
    cols = set(df.columns)
    if not cols:
        return False
    has_year = any("year" in c for c in cols)
    has_geo = any(token in c for c in cols for token in ("country", "area", "territory"))
    has_measure = any(token in c for c in cols for token in ("homicide", "crime", "rate", "count", "victim"))
    return has_year and (has_geo or has_measure)


def _read_unodc_workbook(payload: bytes) -> pd.DataFrame:
    sniff = payload[:256].lstrip().lower()
    if sniff.startswith(b"<!doctype html") or sniff.startswith(b"<html"):
        raise ValueError("UNODC returned HTML instead of an Excel workbook")

    workbook = io.BytesIO(payload)
    errors: list[str] = []
    for engine in ("openpyxl", None):
        try:
            xls = pd.ExcelFile(workbook, engine=engine)
        except Exception as exc:
            errors.append(f"ExcelFile(engine={engine!r}): {exc}")
            workbook.seek(0)
            continue
        for skiprows in (2, 1, 0):
            for sheet_name in xls.sheet_names:
                try:
                    frame = xls.parse(sheet_name=sheet_name, skiprows=skiprows)
                except Exception as exc:
                    errors.append(f"parse(sheet={sheet_name!r}, skiprows={skiprows}): {exc}")
                    continue
                frame = _normalise_frame(frame)
                if _looks_like_unodc_data(frame):
                    return frame
        workbook.seek(0)
    raise ValueError("could not locate a usable UNODC data sheet: " + "; ".join(errors[:6]))


def fetch(series_id: str, **kwargs) -> FetchResult:
    if series_id not in SERIES_MAP:
        raise ValueError(
            f"Unknown UNODC series_id '{series_id}'. Use one of: {list(SERIES_MAP)}"
        )
    url = f"{BASE}/{SERIES_MAP[series_id]}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    # UNODC has changed workbook layouts across vintages; look for the first
    # sheet/skiprow combination that exposes the data block cleanly.
    df = _read_unodc_workbook(r.content)
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
