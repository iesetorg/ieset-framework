"""Chinn-Ito KAOPEN — capital-account-openness index.

Academic-standard de jure capital-account-openness index built from the four
IMF AREAER binary indicators (multiple exchange rates, current-account
restrictions, capital-account restrictions, surrender of export proceeds).
Released annually by Menzie Chinn (UW-Madison / Wisconsin) and Hiro Ito
(Portland State).

Source URL (browser):
    https://web.pdx.edu/~ito/Chinn-Ito_website.htm
    → "kaopen_2023.dta" (or latest year) Stata download

Direct URL: https://web.pdx.edu/~ito/kaopen_2023.dta

Endpoint policy: try the direct URL, fall back to manual-drop
data/manual/chinn_ito/<latest>.dta if upstream is unavailable
(host has been intermittent and is no longer actively maintained).

Series IDs:
    kaopen_index_normalized — main 0-1 normalized index (column `ka_open`)
    kaopen_raw              — un-normalized index (column `kaopen`)
    kaopen_components       — four AREAER binary components (k1,k2,k3,k4)
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import ManualDropError, find_latest

URL = "https://web.pdx.edu/~ito/kaopen_2023.dta"
LICENSE = "academic_citation"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}

SUPPORTED_SERIES = {
    "kaopen_index_normalized",
    "kaopen_raw",
    "kaopen_components",
}

# Column-name heuristics — Chinn-Ito releases have shifted over years:
# kaopen_2023.dta typically ships:  ccode (IFS), country_name, year,
#   kaopen (raw first principal component), ka_open (0-1 normalized),
#   k1, k2, k3, k4 (four AREAER binaries), sd (std dev for raw),
#   plus an ISO/ISO3 column ("ccode_letter" or "iso3") in newer releases.
_NORMALIZED_CANDIDATES = ("ka_open", "kaopen_norm", "kaopen_normalized")
_RAW_CANDIDATES = ("kaopen", "ka_open_raw", "kaopen_raw")
_COMPONENT_CANDIDATES = (("k1", "k2", "k3", "k4"),)
_ISO3_CANDIDATES = ("iso3", "ccode_letter", "country_iso3", "isocode", "wbcode")


def _load_dta() -> tuple[pd.DataFrame, str]:
    """Return (frame, source_url). Try web; fall back to manual drop."""
    try:
        r = requests.get(URL, headers=UA, timeout=60)
        r.raise_for_status()
        df = pd.read_stata(io.BytesIO(r.content), convert_categoricals=False)
        return df, URL
    except (requests.RequestException, ValueError) as exc:  # pragma: no cover
        # Fall back to manual drop. Re-raise with helpful context if missing.
        try:
            path = find_latest("chinn_ito", "dta")
        except ManualDropError as drop_exc:
            raise ManualDropError(
                f"Chinn-Ito direct download failed ({exc!s}). "
                f"{drop_exc}"
            ) from exc
        df = pd.read_stata(path, convert_categoricals=False)
        return df, f"manual://{path.name}"


def _pick(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    cols = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in cols:
            return cols[name.lower()]
    return None


def _standardise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    rename: dict[str, str] = {}
    for c in list(df.columns):
        if isinstance(c, str):
            rename[c] = c.strip()
    df = df.rename(columns=rename)
    iso_col = _pick(df, _ISO3_CANDIDATES)
    if iso_col and iso_col != "country_iso3":
        df = df.rename(columns={iso_col: "country_iso3"})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    return df


def fetch(series_id: str = "kaopen_index_normalized", *, vintage_utc: datetime | None = None) -> FetchResult:
    if series_id not in SUPPORTED_SERIES:
        raise ValueError(
            f"chinn_ito: unsupported series_id '{series_id}'. "
            f"Supported: {sorted(SUPPORTED_SERIES)}"
        )
    fetch_ts = utc_now()
    raw, source_url = _load_dta()
    df = _standardise(raw)

    units: str
    if series_id == "kaopen_index_normalized":
        col = _pick(df, _NORMALIZED_CANDIDATES)
        if col is None:
            raise KeyError(
                f"chinn_ito: normalized index column not found; "
                f"have {list(df.columns)}"
            )
        keep = [c for c in ("country_iso3", "country", "country_name", "ccode", "year") if c in df.columns]
        out = df[keep + [col]].rename(columns={col: "value"})
        units = "0-1 normalized de jure capital-account openness index"
    elif series_id == "kaopen_raw":
        col = _pick(df, _RAW_CANDIDATES)
        if col is None:
            raise KeyError(
                f"chinn_ito: raw index column not found; "
                f"have {list(df.columns)}"
            )
        keep = [c for c in ("country_iso3", "country", "country_name", "ccode", "year") if c in df.columns]
        out = df[keep + [col]].rename(columns={col: "value"})
        units = "first principal component (un-normalized) of four AREAER binary indicators"
    else:  # kaopen_components
        comp_cols: list[str] | None = None
        for cand in _COMPONENT_CANDIDATES:
            if all(c in df.columns for c in cand):
                comp_cols = list(cand)
                break
        if comp_cols is None:
            raise KeyError(
                f"chinn_ito: component columns (k1..k4) not found; "
                f"have {list(df.columns)}"
            )
        keep = [c for c in ("country_iso3", "country", "country_name", "ccode", "year") if c in df.columns]
        out = df[keep + comp_cols]
        units = "binary AREAER components: k1=multiple-FX, k2=current-acct restrictions, k3=capital-acct restrictions, k4=surrender of export proceeds"

    path_out, sha = write_vintage(
        publisher="chinn_ito",
        series_id=series_id,
        frame=out,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "year" in out.columns and out["year"].notna().any():
        start = str(int(out["year"].min()))
        end = str(int(out["year"].max()))

    return FetchResult(
        publisher="chinn_ito",
        series_id=series_id,
        source_url=source_url,
        methodology_url="https://web.pdx.edu/~ito/Chinn-Ito_website.htm",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(out),
        frequency="annual",
        units=units,
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "columns": list(out.columns),
            "raw_columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            "fallback_path": "data/manual/chinn_ito/<latest>.dta if upstream URL fails",
        },
    )
