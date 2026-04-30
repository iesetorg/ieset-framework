"""Kleiner & Krueger occupational-licensing intensity (academic replication).

Source: Morris Kleiner + Alan Krueger, BLS / NBER working papers (2006-2013) and
the Hamilton Project / Brookings 2015 update ("Reforming Occupational Licensing
Policies", The Hamilton Project at Brookings, March 2015).

This is a static academic dataset. There is no public API; the canonical
replication tables ship as appendices to the Brookings update PDF and as small
CSV/Excel files in NBER replication kits. Live URLs are fragile (Brookings has
re-pathed the report twice), so the fetcher tries the documented URLs first and
falls back to a manual-drop pattern.

Manual-drop steps (only needed if the auto-download fails):
1. Create directory: data/manual/kleiner_krueger/
2. From the Hamilton Project / Brookings 2015 update
   ("Reforming Occupational Licensing Policies", Kleiner 2015) extract the
   state-level licensing-share table (Appendix A) and save as
   `kk_state_licensing_share_workforce.csv` with columns
   `state_iso,year,value` (state two-letter, year integer, share in %).
3. From Kleiner & Krueger (2013, "Analyzing the Extent and Influence of
   Occupational Licensing on the Labor Market", J. Labor Econ. v31 S1) save
   the wage-premium table as `kk_licensing_wage_premium.csv` with columns
   `category,year,value` (specification or occupation group, year, % premium).
4. From Kleiner (2000) / Kleiner-Krueger (2010) historical series save the
   occupation-licensing growth table as
   `kk_occupation_licensing_growth_1950_2008.csv` with columns
   `year,share_pct,n_occupations`.
5. From the Brookings 2015 cross-section save
   `kk_state_2015_share_pct.csv` with columns `state_iso,value`.

License: academic / fair use; cite Kleiner & Krueger and the Hamilton Project.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Callable

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import MANUAL_ROOT, ManualDropError

PUBLISHER = "kleiner_krueger"
LICENSE = "academic — Kleiner & Krueger / Hamilton Project; citation required"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) Safari/605.1.15"}
METHODOLOGY_URL = (
    "https://www.hamiltonproject.org/papers/"
    "reforming_occupational_licensing_policies/"
)

# Canonical static URLs for the replication data. These are best-effort: the
# Brookings CMS has re-pathed the report twice since 2015. If a URL 404s we
# fall through to the manual-drop path.
_CANDIDATE_URLS: dict[str, list[str]] = {
    "kk_state_licensing_share_workforce": [
        "https://www.brookings.edu/wp-content/uploads/2016/06/"
        "thp_kleinerdiscpaper_final.csv",
        "https://www.nber.org/system/files/working_papers/w19318/"
        "kleiner_krueger_state_licensing.csv",
    ],
    "kk_licensing_wage_premium": [
        "https://www.nber.org/system/files/working_papers/w14979/"
        "kleiner_krueger_wage_premium.csv",
    ],
    "kk_occupation_licensing_growth_1950_2008": [
        "https://www.nber.org/system/files/working_papers/w14308/"
        "kleiner_occupation_growth.csv",
    ],
    "kk_state_2015_share_pct": [
        "https://www.brookings.edu/wp-content/uploads/2015/03/"
        "thp_kleinerstateshare_2015.csv",
    ],
}

# Per-series metadata exposed to baseline_pull / coverage tooling.
SUPPORTED: dict[str, dict[str, str]] = {
    "kk_state_licensing_share_workforce": {
        "desc": "Kleiner-Krueger state-year share of workforce in licensed "
        "occupations (~50 states x 1983-2015)",
        "frequency": "annual",
        "units": "percent_of_workforce",
        "schema": "state_iso,year,value",
    },
    "kk_licensing_wage_premium": {
        "desc": "Kleiner-Krueger wage premium for licensed vs unlicensed within "
        "occupations (Kleiner-Krueger 2013, JOLE)",
        "frequency": "cross_section",
        "units": "percent_premium",
        "schema": "category,year,value",
    },
    "kk_occupation_licensing_growth_1950_2008": {
        "desc": "Historical growth in % of US workforce in licensed occupations "
        "(Kleiner 2000; Kleiner-Krueger 2010 update)",
        "frequency": "annual",
        "units": "percent_of_workforce",
        "schema": "year,share_pct,n_occupations",
    },
    "kk_state_2015_share_pct": {
        "desc": "Brookings/Hamilton 2015 cross-section: state share of workforce "
        "in licensed occupations (single year)",
        "frequency": "cross_section",
        "units": "percent_of_workforce",
        "schema": "state_iso,value",
    },
}


def _try_download(urls: list[str]) -> tuple[bytes, str] | None:
    for url in urls:
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 200 and len(r.content) > 64:
                return r.content, url
        except requests.RequestException:
            continue
    return None


def _read_csv_bytes(content: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(content))


def _load_manual(series_id: str) -> tuple[pd.DataFrame, str]:
    """Look for `<series_id>.csv` (or .xlsx) under data/manual/kleiner_krueger/."""
    pub_dir = MANUAL_ROOT / PUBLISHER
    if not pub_dir.exists():
        raise ManualDropError(
            f"No manual-drop dir for '{PUBLISHER}'. See module docstring for "
            f"steps; expected directory: {pub_dir}"
        )
    for ext in ("csv", "xlsx", "xls"):
        candidate = pub_dir / f"{series_id}.{ext}"
        if candidate.exists():
            if ext == "csv":
                return pd.read_csv(candidate), f"manual://{candidate}"
            return pd.read_excel(candidate), f"manual://{candidate}"
    raise ManualDropError(
        f"No manual file for '{series_id}' in {pub_dir}. Expected one of "
        f"{series_id}.csv / .xlsx / .xls"
    )


# ---------------------------------------------------------------------------
# Per-series normalisers — bring whatever we got into the documented schema.
# ---------------------------------------------------------------------------

def _norm_state_year(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns if isinstance(c, str)})
    # Accept common variants
    rn = {}
    for c in df.columns:
        if c in {"state", "state_abbr", "stateabbr", "state_code"}:
            rn[c] = "state_iso"
        elif c in {"yr", "year_id"}:
            rn[c] = "year"
        elif c in {"share", "licensed_share", "pct", "percent", "share_pct"}:
            rn[c] = "value"
    df = df.rename(columns=rn)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def _norm_wage_premium(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns if isinstance(c, str)})
    rn = {}
    for c in df.columns:
        if c in {"specification", "spec", "occupation", "group"}:
            rn[c] = "category"
        elif c in {"premium", "wage_premium", "pct", "percent"}:
            rn[c] = "value"
    df = df.rename(columns=rn)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def _norm_growth(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns if isinstance(c, str)})
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def _norm_state_2015(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={c: c.strip().lower() for c in df.columns if isinstance(c, str)})
    rn = {}
    for c in df.columns:
        if c in {"state", "state_abbr", "stateabbr", "state_code"}:
            rn[c] = "state_iso"
        elif c in {"share", "licensed_share", "pct", "percent", "share_pct"}:
            rn[c] = "value"
    df = df.rename(columns=rn)
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


_NORMALISERS: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "kk_state_licensing_share_workforce": _norm_state_year,
    "kk_licensing_wage_premium": _norm_wage_premium,
    "kk_occupation_licensing_growth_1950_2008": _norm_growth,
    "kk_state_2015_share_pct": _norm_state_2015,
}


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    if series_id not in SUPPORTED:
        raise ValueError(
            f"Unsupported Kleiner-Krueger series '{series_id}'. "
            f"Supported: {sorted(SUPPORTED)}"
        )
    fetch_ts = utc_now()
    meta = SUPPORTED[series_id]

    downloaded = _try_download(_CANDIDATE_URLS.get(series_id, []))
    if downloaded is not None:
        content, source_url = downloaded
        df = _read_csv_bytes(content)
    else:
        df, source_url = _load_manual(series_id)

    df = _NORMALISERS[series_id](df)

    path_out, sha = write_vintage(
        publisher=PUBLISHER,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start_year = end_year = None
    if "year" in df.columns and df["year"].notna().any():
        start_year = str(int(df["year"].min()))
        end_year = str(int(df["year"].max()))

    return FetchResult(
        publisher=PUBLISHER,
        series_id=series_id,
        source_url=source_url,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta["frequency"],
        units=meta["units"],
        currency=None,
        start_date=start_year,
        end_date=end_year,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "schema": meta["schema"],
            "columns": list(df.columns),
            "manual_drop_used": source_url.startswith("manual://"),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
