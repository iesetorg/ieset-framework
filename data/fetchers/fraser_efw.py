"""Fraser Institute Economic Freedom of the World fetcher.

Auto-download path (preferred):
  Discovered via web search: the master xlsx is served from a static Drupal
  file path on efotw.org:
    https://efotw.org/sites/all/modules/custom/ftw_maps_pages/files/
    efotw-{YEAR}-master-index-data-for-researchers-iso.xlsx
  Verified working for 2025 (curl_cffi Chrome impersonation, 200 OK, 5.4 MB).
  Earlier years (2023, 2024) 404 — Fraser only keeps the latest edition.

Fallback path:
  If auto-download fails (e.g. URL pattern changes), users can drop the file
  into data/manual/fraser_efw/ and the fetcher will use it.

Historical context (kept for transparency):
  The Fraser dataset page (fraserinstitute.org and efotw.org) is guarded by
  Cloudflare JS challenge, which blocks plain requests, curl_cffi without
  impersonation, and Playwright. The page also has no xlsx links in static
  HTML — the download button triggers a JS flow. The static file path above
  bypasses all of this.
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from curl_cffi import requests as cffi_requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic_citation"
MANUAL_DIR = Path(__file__).resolve().parents[2] / "data" / "manual" / "fraser_efw"
PANEL_SHEET = "EFW Panel Dataset"
AUTO_BASE = (
    "https://efotw.org/sites/all/modules/custom/ftw_maps_pages/files/"
    "efotw-{year}-master-index-data-for-researchers-iso.xlsx"
)


class FraserError(RuntimeError):
    pass


def _auto_download(year: str) -> bytes | None:
    """Try to download the master xlsx directly. Returns bytes or None."""
    url = AUTO_BASE.format(year=year)
    try:
        r = cffi_requests.get(url, impersonate="chrome", timeout=60)
        if r.status_code == 200 and len(r.content) > 1_000_000:
            return r.content
    except Exception:
        pass
    return None


def _latest_manual_xlsx() -> Path:
    if not MANUAL_DIR.exists():
        raise FraserError(
            f"No Fraser EFW xlsx found. Auto-download also failed. "
            f"Download from https://www.fraserinstitute.org/economic-freedom/dataset "
            f"and drop into {MANUAL_DIR}"
        )
    candidates = sorted(MANUAL_DIR.glob("*.xlsx"))
    if not candidates:
        raise FraserError(f"No .xlsx in {MANUAL_DIR} — drop Fraser EFW file there")
    return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))


def fetch(series_id: str = "efw_panel", *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: 'efw_panel' (tidy panel) | 'efw_index_detail' (wide 87-col sheet).

    Tries auto-download first; falls back to manual drop directory.
    """
    fetch_ts = utc_now()
    year = series_id.split("_")[-1] if series_id.startswith("efw_") and series_id[-1:].isdigit() else "2025"

    # Try auto-download
    raw = _auto_download(year)
    source_url = AUTO_BASE.format(year=year)
    if raw is None:
        # Try latest year as fallback
        raw = _auto_download("2025")
        if raw:
            source_url = AUTO_BASE.format(year="2025")
    auto_downloaded = raw is not None
    if raw is None:
        xlsx_path = _latest_manual_xlsx()
        raw = xlsx_path.read_bytes()
        source_url = f"manual://{xlsx_path.name}"

    xls = pd.ExcelFile(io.BytesIO(raw))

    if series_id == "efw_panel" or series_id.startswith("efw_20"):
        if PANEL_SHEET not in xls.sheet_names:
            raise FraserError(f"Sheet '{PANEL_SHEET}' not in downloaded file; sheets: {xls.sheet_names}")
        df = xls.parse(PANEL_SHEET)
        df = df.rename(columns={
            "ISO_Code": "country_iso3",
            "Countries": "country_name",
            "Year": "year",
            "Summary": "efw_summary",
            "Area 1": "area_1_size_of_government",
            "Area 2": "area_2_legal_system_property_rights",
            "Area 3": "area_3_sound_money",
            "Area 4": "area_4_freedom_to_trade_internationally",
            "Area 5": "area_5_regulation",
            "Standard Deviation of the 5 EFW Areas": "area_stdev",
            "World Bank Region": "wb_region",
            "World Bank Current Income Classification, 1990-Present": "wb_income_class",
        })
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        for c in ("efw_summary", "area_1_size_of_government", "area_2_legal_system_property_rights",
                  "area_3_sound_money", "area_4_freedom_to_trade_internationally",
                  "area_5_regulation", "area_stdev"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        for c in df.columns:
            if df[c].dtype == "object":
                df[c] = df[c].astype("string")
        frequency = "annual"
    elif series_id == "efw_index_detail":
        candidate = next(
            (s for s in xls.sheet_names if "index" in s.lower() and any(y in s for y in ["1970", "1980", "1990"])),
            None,
        )
        if not candidate:
            raise FraserError(f"Detail sheet not found in downloaded file")
        df = xls.parse(candidate, header=2)
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
        for c in list(df.columns):
            if df[c].dtype == "object":
                df[c] = df[c].astype("string")
        frequency = "annual"
    else:
        raise FraserError(f"unknown series_id {series_id!r}; one of: efw_panel, efw_index_detail, efw_2025")

    path_out, sha = write_vintage(
        publisher="fraser_efw",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    year_col = "year" if "year" in df.columns else None
    start = int(df[year_col].min()) if year_col and df[year_col].notna().any() else None
    end = int(df[year_col].max()) if year_col and df[year_col].notna().any() else None

    return FetchResult(
        publisher="fraser_efw",
        series_id=series_id,
        source_url=source_url,
        methodology_url="https://www.fraserinstitute.org/economic-freedom/approach",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=frequency,
        units="Index 0-10 (higher = more economic freedom); sub-area components per methodology",
        currency=None,
        start_date=str(start) if start else None,
        end_date=str(end) if end else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "auto_download": auto_downloaded,
            "sheet": PANEL_SHEET if series_id == "efw_panel" else "EFW Index 1970-2023",
            "n_columns": len(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
