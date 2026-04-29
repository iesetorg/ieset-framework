"""Fraser Institute Economic Freedom of the World fetcher.

Cloudflare JS challenge blocks every automated-access path we probed
(plain requests, curl_cffi Chrome/Safari fingerprint, Playwright plain +
stealth). The dataset page also returns zero xlsx/download-action links
in rendered HTML, suggesting the URL is generated post-click via a flow
we haven't reverse-engineered.

Interim solution: users download the master xlsx manually from
https://www.fraserinstitute.org/economic-freedom/dataset and drop it into
data/manual/fraser_efw/ with the publisher's filename convention
(e.g. efotw-2025-master-index-data-for-researchers-iso.xlsx). This
fetcher picks the latest file matching the pattern and parses the
'EFW Panel Dataset' sheet (ISO_Code, Countries, Year, Summary, Area 1-5,
etc.) as the canonical tidy panel.

Alternate: if a ZENROWS_API_KEY env var is set, the fetcher can attempt
a Zenrows-proxied download — implementation deferred until the manual
route is exercised.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "academic_citation"
MANUAL_DIR = Path(__file__).resolve().parents[2] / "data" / "manual" / "fraser_efw"
PANEL_SHEET = "EFW Panel Dataset"


class FraserError(RuntimeError):
    pass


def _latest_manual_xlsx() -> Path:
    if not MANUAL_DIR.exists():
        raise FraserError(
            f"No Fraser EFW xlsx found. Download from "
            f"https://www.fraserinstitute.org/economic-freedom/dataset and "
            f"drop into {MANUAL_DIR.relative_to(MANUAL_DIR.parents[3])}"
        )
    candidates = sorted(MANUAL_DIR.glob("*.xlsx"))
    if not candidates:
        raise FraserError(f"No .xlsx in {MANUAL_DIR} — drop Fraser EFW file there")
    # Latest by filename (Fraser names include year) falling back to mtime
    return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))


def fetch(series_id: str = "efw_panel", *, vintage_utc: datetime | None = None) -> FetchResult:
    """series_id: 'efw_panel' (tidy panel) | 'efw_index_detail' (wide 87-col sheet).

    Reads from data/manual/fraser_efw/ — manual drop required since Fraser's
    dataset page is Cloudflare-JS-gated and direct xlsx URLs 403.
    """
    xlsx_path = _latest_manual_xlsx()
    fetch_ts = utc_now()
    xls = pd.ExcelFile(xlsx_path)

    if series_id == "efw_panel":
        if PANEL_SHEET not in xls.sheet_names:
            raise FraserError(f"Sheet '{PANEL_SHEET}' not in {xlsx_path.name}; sheets: {xls.sheet_names}")
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
        # Wide 87-column detail sheet with Area sub-components. Fraser ships
        # this with 3-row header (title / category / metric), which pandas
        # MultiIndex flattening handles poorly — we read with header=2 and
        # keep the single-row metric labels; upstream users who need the
        # area-grouping can parse from the EFW Index 1970-2023 sheet directly.
        candidate = next(
            (s for s in xls.sheet_names if "index" in s.lower() and any(y in s for y in ["1970", "1980", "1990"])),
            None,
        )
        if not candidate:
            raise FraserError(f"Detail sheet not found in {xlsx_path.name}")
        df = xls.parse(candidate, header=2)
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
        for c in list(df.columns):
            if df[c].dtype == "object":
                df[c] = df[c].astype("string")
        frequency = "annual"
    else:
        raise FraserError(f"unknown series_id {series_id!r}; one of: efw_panel, efw_index_detail")

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
        source_url=f"manual://{xlsx_path.name}",
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
            "manual_file": xlsx_path.name,
            "sheet": PANEL_SHEET if series_id == "efw_panel" else "EFW Index 1970-2023",
            "n_columns": len(df.columns),
            "manual_drop_dir": str(MANUAL_DIR.relative_to(MANUAL_DIR.parents[3])),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
