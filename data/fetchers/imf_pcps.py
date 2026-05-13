"""IMF Primary Commodity Price System (PCPS) fetcher.

Source page:
    https://www.imf.org/en/research/commodity-prices

The public IMF commodity-prices portal links a monthly Excel workbook:
    https://www.imf.org/-/media/files/research/commodityprices/monthly/external-data.xls

The workbook contains a single "External" sheet with:
    row 0 -> indicator code
    row 1 -> indicator description
    row 2 -> unit / data type
    row 3 -> frequency
    row 4+ -> period + values

Some legacy hypotheses refer to informal aliases rather than workbook codes
(`Primary`, `Oil`, `PNG_USD`). We preserve those aliases here so existing specs
become fetchable without an immediate rewrite.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

WORKBOOK_URL = "https://www.imf.org/-/media/files/research/commodityprices/monthly/external-data.xls"
SOURCE_PAGE_URL = "https://www.imf.org/en/research/commodity-prices"
TECHNICAL_DOC_URL = "https://www.imf.org/-/media/files/research/commodityprices/monthly/pcps-technical-documentation.pdf"
METHODOLOGY = "https://www.imf.org/en/Research/commodity-prices"
LICENSE = "IMF standard permissions (attribution required)"
SHEET_NAME = "External"

SERIES_ALIASES = {
    # Legacy spec shorthands.
    "PRIMARY": "PALLFNF",
    "OIL": "POILAPSP",
    "PNG_USD": "PNGASEU",
    "PNGASEUUSDM": "PNGASEU",
    "PCOPPUSDM": "PCOPP",
}


class ImfPcpsError(RuntimeError):
    pass


def _get_workbook() -> pd.DataFrame:
    r = requests.get(WORKBOOK_URL, timeout=120)
    r.raise_for_status()
    return pd.read_excel(io.BytesIO(r.content), sheet_name=SHEET_NAME, header=None)


def _infer_frequency(periods: pd.Series) -> str:
    s = periods.astype(str)
    if s.str.contains("M", na=False).any():
        return "monthly"
    if s.str.contains("Q", na=False).any():
        return "quarterly"
    return "annual"


def _canonical_series_id(series_id: str) -> str:
    raw = str(series_id or "").strip()
    upper = raw.upper()
    if not upper:
        raise ImfPcpsError("Missing PCPS series_id")
    return SERIES_ALIASES.get(upper, upper)


def _resolve_column(sheet: pd.DataFrame, series_id: str) -> tuple[int, str, str, str]:
    codes = sheet.iloc[0].astype(str).str.strip()
    descriptions = sheet.iloc[1].astype(str).str.strip()
    units = sheet.iloc[2].astype(str).str.strip()
    frequencies = sheet.iloc[3].astype(str).str.strip()

    matches = [idx for idx, code in enumerate(codes) if code.upper() == series_id]
    if not matches:
        available = sorted({code for code in codes if code and code != "nan"})
        raise ImfPcpsError(
            f"IMF PCPS series {series_id} not found in workbook. "
            f"Available examples: {', '.join(available[:20])}"
        )

    # Some codes appear twice: once as an empty index column and once as the
    # usable USD-priced series. Prefer the column with more non-null data rows.
    best_idx = max(matches, key=lambda idx: int(sheet.iloc[4:, idx].notna().sum()))
    return best_idx, descriptions.iloc[best_idx], units.iloc[best_idx], frequencies.iloc[best_idx]


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch a PCPS commodity series from the IMF workbook."""
    fetch_ts = utc_now()
    canonical = _canonical_series_id(series_id)
    sheet = _get_workbook()
    col_idx, description, unit, frequency_label = _resolve_column(sheet, canonical)

    period_col = sheet.iloc[4:, 0].astype(str).str.strip()
    value_col = pd.to_numeric(sheet.iloc[4:, col_idx], errors="coerce")
    df = pd.DataFrame({
        "region": "W00",
        "period": period_col,
        "value": value_col,
    })
    df = df[df["period"].notna() & (df["period"] != "") & (df["period"] != "nan")]
    df = df.dropna(subset=["value"]).reset_index(drop=True)
    if df.empty:
        raise ImfPcpsError(f"IMF PCPS workbook contains no usable observations for {canonical}")

    path_out, sha = write_vintage(
        publisher="imf_pcps",
        series_id=canonical,
        frame=df,
        fetch_utc=fetch_ts,
    )
    frequency = str(frequency_label).lower() if frequency_label and frequency_label != "nan" else _infer_frequency(df["period"])
    unit_text = str(unit).strip()
    currency = "USD" if "usd" in unit_text.lower() or "us$" in description.lower() else None

    return FetchResult(
        publisher="imf_pcps",
        series_id=canonical,
        source_url=WORKBOOK_URL,
        methodology_url=TECHNICAL_DOC_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=frequency,
        units=unit_text or "per indicator definition",
        currency=currency,
        start_date=str(df["period"].min()) if len(df) else None,
        end_date=str(df["period"].max()) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "indicator_label": description or canonical,
            "dataset": "PCPS",
            "requested_series_id": series_id,
            "resolved_series_id": canonical,
            "source_page_url": SOURCE_PAGE_URL,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
