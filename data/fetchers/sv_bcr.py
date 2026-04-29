"""Banco Central de Reserva de El Salvador (BCR) — manual-drop fetcher.

Source URLs (browser):
    https://www.bcr.gob.sv/bcrsite/                       — main portal
    https://www.bcr.gob.sv/en/estadisticas-y-publicaciones — statistics + publications
    https://www.bcr.gob.sv/regulaciones/upload_files/      — bulk file repository

BCR ships its statistical bulletins as PDF reports + Excel sheets linked
from publication pages. There is no public REST/SDMX API. Direct file
URLs rotate per release vintage and the publication index is rendered
client-side, so automated discovery is brittle. Manual-drop is the
realistic pattern (mirrors data/fetchers/boj.py for BoJ stat-search):
the user downloads the latest workbook from the BCR website and drops
it into ``data/manual/sv_bcr/`` under a filename matching one of the
SUPPORTED series prefixes below.

Canonical series for IESET:

    pib_real_quarterly    — Real GDP, quarterly, current methodology
                            (Cuentas Nacionales Trimestrales — PIB encadenado)
    inflation_cpi         — IPC (Indice de Precios al Consumidor),
                            monthly, year-over-year inflation
    fdi_inflows           — IED (Inversion Extranjera Directa), inflows,
                            quarterly, USD millions
    monetary_aggregates   — Sistema Financiero — depositos / liquidez
                            (M1/M2/M3 equivalents), monthly, USD millions
                            (El Salvador is dollarised since 2001 so all
                            balance-sheet aggregates are USD-denominated)

Filename convention under data/manual/sv_bcr/:

    pib_real_quarterly_<vintage>.xlsx
    inflation_cpi_<vintage>.xlsx
    fdi_inflows_<vintage>.xlsx
    monetary_aggregates_<vintage>.xlsx

If a series-specific file is not found, the fetcher falls back to the
latest file in the directory (any extension) so partial drops still
resolve, mirroring the BoJ pattern.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError, find_latest

LICENSE = "BCR — public, citation required"
METHODOLOGY = "https://www.bcr.gob.sv/en/estadisticas-y-publicaciones"

# series_id -> (frequency, units, currency, filename-prefix hint)
SUPPORTED: dict[str, dict[str, str]] = {
    "pib_real_quarterly": {
        "frequency": "quarterly",
        "units": "Real GDP, chained-volume index (PIB encadenado, base 2014)",
        "currency": "USD",
        "prefix": "pib_real_quarterly",
    },
    "inflation_cpi": {
        "frequency": "monthly",
        "units": "IPC index + year-over-year percent change",
        "currency": "USD",
        "prefix": "inflation_cpi",
    },
    "fdi_inflows": {
        "frequency": "quarterly",
        "units": "Foreign Direct Investment inflows, USD millions",
        "currency": "USD",
        "prefix": "fdi_inflows",
    },
    "monetary_aggregates": {
        "frequency": "monthly",
        "units": "Banking-system deposits / liquidity aggregates, USD millions",
        "currency": "USD",
        "prefix": "monetary_aggregates",
    },
}


def _resolve_path(series_id: str) -> Path:
    """Find the latest file matching the series prefix, else fall back to
    the latest file of any kind in data/manual/sv_bcr/."""
    pub_dir = MANUAL_ROOT / "sv_bcr"
    spec = SUPPORTED.get(series_id)
    if spec and pub_dir.exists():
        prefix = spec["prefix"]
        exts = (".xlsx", ".xls", ".csv")
        candidates = [
            p for p in pub_dir.iterdir()
            if p.is_file()
            and not p.name.startswith(".")
            and p.suffix.lower() in exts
            and p.stem.lower().startswith(prefix.lower())
        ]
        if candidates:
            return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))
    # Fallback: latest file of any supported extension.
    return find_latest("sv_bcr", "xlsx", "xls", "csv")


def fetch(
    series_id: str = "pib_real_quarterly",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in SUPPORTED:
        raise ManualDropError(
            f"Unknown sv_bcr series_id={series_id!r}. "
            f"Supported: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    path = _resolve_path(series_id)
    fetch_ts = utc_now()
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    out, sha = write_vintage(
        publisher="sv_bcr", series_id=series_id, frame=df, fetch_utc=fetch_ts
    )
    return FetchResult(
        publisher="sv_bcr",
        series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec["frequency"],
        units=spec["units"],
        currency=spec["currency"],
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=out,
        extra={
            "manual_file": path.name,
            "n_columns": len(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            "country_iso3": "SLV",
        },
    )
