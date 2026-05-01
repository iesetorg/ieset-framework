"""V-Dem (Varieties of Democracy) fetcher.

Primary source: the vdeminstitute/vdemdata GitHub repo mirror of the
country-year dataset. V-Dem's main portal (v-dem.net) gates downloads
behind a front-end flow; the R-package mirror is open and stable.

Supports series_ids:
    vdem_cy_full     Full country-year dataset (v2*, etc., 500+ columns)
    codebook         Variable-level metadata

Fetches RData, parses via ``pyreadr`` when available and falls back to the
pure-Python ``rdata`` package otherwise, then writes parquet. The full dataset
is ~34MB on disk; compressed parquet lands at ~25-40MB.

License: academic; citation required (Coppedge, Gerring, Lindberg, Skaaning,
Teorell, et al. 2024). Free use with citation.
"""
from __future__ import annotations

import io
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

RAW_BASE = "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data"
LICENSE = "academic — V-Dem Institute; citation required"

SERIES = {
    "vdem_cy_full": ("vdem.RData",      "V-Dem country-year full dataset (1789-present, ~500 columns)"),
    "codebook":      ("codebook.RData",  "V-Dem variable codebook"),
    "vparty":        ("vparty.RData",    "V-Party country-year dataset"),
}


class VdemError(RuntimeError):
    pass


def _load_rdata_frame(path: Path) -> tuple[str, pd.DataFrame, str]:
    """Load the first tabular object from a V-Dem RData file."""
    try:
        import pyreadr  # type: ignore

        result = pyreadr.read_r(str(path))
        backend = "pyreadr"
    except ImportError:
        try:
            import rdata  # type: ignore
        except ImportError as e:
            raise VdemError(
                "Neither pyreadr nor rdata is installed; install one to parse V-Dem RData"
            ) from e
        result = rdata.read_rda(str(path))
        backend = "rdata"

    if not result:
        raise VdemError(f"RData parser returned no objects from {path.name}")

    key = next(iter(result))
    df = result[key]
    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception as e:  # pragma: no cover - defensive conversion
            raise VdemError(f"V-Dem object {key!r} is not a usable DataFrame") from e
    if df.empty:
        raise VdemError(f"V-Dem {path.name} -> {key} is empty")
    return key, df, backend


def _fetch_full_dataset() -> tuple[pd.DataFrame, str, str]:
    """Fetch and parse the vdem_cy_full RData, returning (df, key, backend)."""
    filename, desc = SERIES["vdem_cy_full"]
    url = f"{RAW_BASE}/{filename}"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as tmp:
        tmp.write(r.content)
        tmp_path = Path(tmp.name)
    try:
        key, df, backend = _load_rdata_frame(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return df, key, backend


_VDEM_FULL_CACHE: tuple[pd.DataFrame, str, str] | None = None


def _get_full_dataset() -> tuple[pd.DataFrame, str, str]:
    global _VDEM_FULL_CACHE
    if _VDEM_FULL_CACHE is None:
        _VDEM_FULL_CACHE = _fetch_full_dataset()
    return _VDEM_FULL_CACHE


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id in SERIES:
        return _fetch_builtin(series_id, vintage_utc=vintage_utc)

    # Try pseudo-series: a column name inside vdem_cy_full
    df_full, key, backend = _get_full_dataset()
    if series_id in df_full.columns:
        return _fetch_pseudo_series(series_id, df_full, key, backend, vintage_utc=vintage_utc)

    raise VdemError(
        f"unknown V-Dem series_id {series_id!r}; one of {list(SERIES)} or a column in vdem_cy_full"
    )


def _fetch_builtin(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    filename, desc = SERIES[series_id]
    url = f"{RAW_BASE}/{filename}"

    fetch_ts = utc_now()
    r = requests.get(url, timeout=120)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as tmp:
        tmp.write(r.content)
        tmp_path = Path(tmp.name)
    try:
        key, df, backend = _load_rdata_frame(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    path_out, sha = write_vintage(
        publisher="vdem",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    year_col = next((c for c in ("year", "Year", "YEAR") if c in df.columns), None)
    start = str(df[year_col].min()) if year_col else None
    end = str(df[year_col].max()) if year_col else None

    return FetchResult(
        publisher="vdem",
        series_id=series_id,
        source_url=url,
        methodology_url="https://v-dem.net/data/reference-documents/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual" if year_col else "unknown",
        units="per variable (see codebook)",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "rdata_object_key": key,
            "parser_backend": backend,
            "n_columns": len(df.columns),
            "description": desc,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _fetch_pseudo_series(
    series_id: str,
    df_full: pd.DataFrame,
    key: str,
    backend: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Extract a single column from the full V-Dem dataset as its own series."""
    fetch_ts = utc_now()
    # Keep identifying columns + the requested variable
    keep_cols = [c for c in ("country_id", "country_text_id", "year", "Year", "YEAR") if c in df_full.columns]
    if series_id not in keep_cols:
        keep_cols.append(series_id)
    df = df_full[keep_cols].copy()

    path_out, sha = write_vintage(
        publisher="vdem",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    year_col = next((c for c in ("year", "Year", "YEAR") if c in df.columns), None)
    start = str(df[year_col].min()) if year_col else None
    end = str(df[year_col].max()) if year_col else None

    return FetchResult(
        publisher="vdem",
        series_id=series_id,
        source_url=f"{RAW_BASE}/vdem.RData",
        methodology_url="https://v-dem.net/data/reference-documents/",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual" if year_col else "unknown",
        units="per variable (see codebook)",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "rdata_object_key": key,
            "parser_backend": backend,
            "n_columns": len(df.columns),
            "description": f"V-Dem column '{series_id}' extracted from vdem_cy_full",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
