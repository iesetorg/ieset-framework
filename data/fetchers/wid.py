"""World Inequality Database (WID) fetcher.

Source page:
    https://wid.world/data/

The WID frontend exposes direct bulk files under:
    https://wid.world/bulk_download/

Useful patterns discovered from the live site JS:
    wid_all_data.zip
    WID_fulldataset_<ISO2>.zip

We prefer country-targeted ZIPs when ``country_filter`` is supplied to avoid
downloading the full all-country archive unnecessarily. Manual-drop files under
``data/manual/wid`` remain a fallback.
"""
from __future__ import annotations

import contextlib
import zipfile
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"
SOURCE_PAGE_URL = "https://wid.world/data/"
BULK_ROOT_URL = "https://wid.world/bulk_download/"
FULL_BULK_URL = f"{BULK_ROOT_URL}wid_all_data.zip"
SERIES_ALIASES = {
    "top-0-1-share-of-total-income": "top_0p1_share_pretax_income",
}
SUPPORTED = {
    "wid_all": "Full WID bulk export",
    "top_0p1_share_pretax_income": "Top 0.1% pre-tax national income share (WID bulk extract)",
    "top-0-1-share-of-total-income": "Alias for top_0p1_share_pretax_income",
}
SERIES_SPECS = {
    "top_0p1_share_pretax_income": {
        "variables": ["sptincj999", "sptincj992"],
        "percentile": "p99.9p100",
        "scale": 100.0,
        "units": "share of pre-tax national income (%)",
    },
}


def _download_to_temp(url: str) -> Path:
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    tmp = NamedTemporaryFile(prefix="wid_", suffix=".zip", delete=False)
    with tmp:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                tmp.write(chunk)
    return Path(tmp.name)


def _resolve_input_paths(country_filter: list[str] | None) -> tuple[list[Path], str]:
    if country_filter:
        paths = []
        urls = []
        for code in country_filter:
            code = str(code).strip().upper()
            if not code:
                continue
            url = f"{BULK_ROOT_URL}WID_fulldataset_{code}.zip"
            paths.append(_download_to_temp(url))
            urls.append(url)
        if paths:
            return paths, "; ".join(urls)
    try:
        return [find_latest("wid", "zip", "csv")], "manual"
    except FileNotFoundError:
        return [_download_to_temp(FULL_BULK_URL)], FULL_BULK_URL


def _extract_series(df: pd.DataFrame, series_id: str) -> pd.DataFrame:
    spec = SERIES_SPECS[series_id]
    if "variable" not in df.columns or "percentile" not in df.columns:
        raise RuntimeError(f"WID bulk extract missing variable/percentile columns for {series_id}")
    sub = df[
        df["variable"].isin(spec["variables"])
        & (df["percentile"].astype("string") == spec["percentile"])
    ].copy()
    if sub.empty:
        raise RuntimeError(f"WID bulk extract had no rows for {series_id}")
    sub["country"] = sub["country"].astype("string")
    sub["year"] = pd.to_numeric(sub["year"], errors="coerce").astype("Int64")
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce") * float(spec.get("scale", 1.0))
    priority = {name: idx for idx, name in enumerate(spec["variables"])}
    sub["_priority"] = sub["variable"].map(priority).fillna(len(priority)).astype(int)
    sub = sub.dropna(subset=["country", "year", "value"])
    sub = (
        sub.sort_values(["country", "year", "_priority"])
        .drop_duplicates(subset=["country", "year"], keep="first")
        [["country", "year", "value"]]
        .reset_index(drop=True)
    )
    return sub


def fetch(
    series_id: str = "wid_all",
    *,
    vintage_utc: datetime | None = None,
    country_filter: list[str] | None = None,
) -> FetchResult:
    """Load WID bulk data.

    series_id='wid_all' concatenates every country CSV in the zip; users
    typically then filter to the variables + countries they need.
    country_filter: optional list of ISO2 codes (WID uses ISO2, not ISO3).
    """
    fetch_ts = utc_now()
    requested_series = series_id
    series_id = SERIES_ALIASES.get(series_id, series_id)
    paths, source_url = _resolve_input_paths(country_filter)

    frames = []
    try:
        for path in paths:
            if path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path) as zf:
                    csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                    if country_filter:
                        wanted = {str(c).strip().upper() for c in country_filter if str(c).strip()}
                        csvs = [
                            n for n in csvs
                            if any(
                                Path(n).stem.upper().endswith(f"_{code}")
                                or Path(n).name.upper() in {f"{code}.CSV", f"{code}_METADATA.CSV"}
                                for code in wanted
                            )
                            or Path(n).name.upper() == "WID_COUNTRIES.CSV"
                        ]
                    for n in csvs:
                        with zf.open(n) as f:
                            try:
                                d = pd.read_csv(f, sep=None, engine="python", on_bad_lines="skip")
                                d["__file"] = n
                                frames.append(d)
                            except Exception:
                                continue
            else:
                frames.append(pd.read_csv(path))
    finally:
        for path in paths:
            if source_url != "manual":
                with contextlib.suppress(FileNotFoundError):
                    path.unlink()

    if not frames:
        joined = ", ".join(p.name for p in paths)
        raise RuntimeError(f"No CSVs parsed from {joined}")
    df = pd.concat(frames, ignore_index=True)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    units = "per variable (income shares %, wealth-to-income ratios, etc.)"
    if series_id != "wid_all":
        if series_id not in SERIES_SPECS:
            raise RuntimeError(
                f"Unsupported WID series_id '{requested_series}'. Supported: {sorted(SUPPORTED)}"
            )
        df = _extract_series(df, series_id)
        units = SERIES_SPECS[series_id]["units"]

    out, sha = write_vintage(publisher="wid", series_id=requested_series, frame=df, fetch_utc=fetch_ts)
    start = end = None
    if "year" in df.columns and df["year"].notna().any():
        start = str(int(df["year"].min()))
        end = str(int(df["year"].max()))
    return FetchResult(
        publisher="wid", series_id=requested_series,
        source_url=SOURCE_PAGE_URL if source_url == "manual" else source_url,
        methodology_url="https://wid.world/methodology/",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units=units,
        currency=None, start_date=start, end_date=end,
        sha256=sha, parquet_path=out,
        extra={
            "resolved_series_id": series_id,
            "source_mode": "manual" if source_url == "manual" else "remote_bulk_download",
            "source_paths": [p.name for p in paths],
            "country_filter": country_filter,
            "n_files_ingested": len(frames),
            "n_columns": len(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
