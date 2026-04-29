"""World Inequality Database (WID) — manual-drop fetcher.

Source URL (browser):
    https://wid.world/data/ → "Bulk Download" (zip of CSVs)

WID bulk paths 404 on every URL probed (their internal storage obfuscates
filenames). Drop the wid bulk zip into data/manual/wid/.

Contents: per-country CSVs with income/wealth shares by percentile, labor
income shares, wealth-to-income ratios, etc. Gold standard for
distributional work.
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._manual_utils import find_latest

LICENSE = "academic_citation"


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
    path = find_latest("wid", "zip", "csv")
    fetch_ts = utc_now()

    frames = []
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if country_filter:
                csvs = [n for n in csvs if any(f"_{c}" in n or f"/{c}" in n or n.startswith(c) for c in country_filter)]
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

    if not frames:
        raise RuntimeError(f"No CSVs parsed from {path.name}")
    df = pd.concat(frames, ignore_index=True)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")

    out, sha = write_vintage(publisher="wid", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="wid", series_id=series_id,
        source_url=f"manual://{path.name}",
        methodology_url="https://wid.world/methodology/",
        license=LICENSE, fetch_utc=fetch_ts,
        rows=len(df), frequency="annual",
        units="per variable (income shares %, wealth-to-income ratios, etc.)",
        currency=None, start_date=None, end_date=None,
        sha256=sha, parquet_path=out,
        extra={"manual_file": path.name, "n_files_ingested": len(frames), "country_filter": country_filter,
               "n_columns": len(df.columns),
               "vintage_utc": vintage_utc.isoformat() if vintage_utc else None},
    )
