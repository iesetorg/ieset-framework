"""V-Dem (Varieties of Democracy) fetcher.

Primary source: the vdeminstitute/vdemdata GitHub repo mirror of the
country-year dataset. V-Dem's main portal (v-dem.net) gates downloads
behind a front-end flow; the R-package mirror is open and stable.

Supports series_ids:
    vdem_cy_full     Full country-year dataset (v2*, etc., 500+ columns)
    codebook         Variable-level metadata

Fetches RData, parses via pyreadr, writes parquet. The full dataset is ~34MB
on disk; compressed parquet lands at ~25-40MB.

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


def fetch(
    series_id: Literal["vdem_cy_full", "codebook", "vparty"],
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    if series_id not in SERIES:
        raise VdemError(f"unknown V-Dem series_id {series_id!r}; one of {list(SERIES)}")
    try:
        import pyreadr  # type: ignore
    except ImportError as e:
        raise VdemError("pyreadr not installed; pip install pyreadr") from e

    filename, desc = SERIES[series_id]
    url = f"{RAW_BASE}/{filename}"

    fetch_ts = utc_now()
    r = requests.get(url, timeout=120)
    r.raise_for_status()

    # pyreadr reads from a filesystem path — dump to a temp file, parse, discard.
    with tempfile.NamedTemporaryFile(suffix=".RData", delete=False) as tmp:
        tmp.write(r.content)
        tmp_path = Path(tmp.name)
    try:
        result = pyreadr.read_r(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)

    if not result:
        raise VdemError(f"pyreadr returned no data frames from {filename}")
    # V-Dem RData ships one named data frame ('vdem' / 'codebook' / 'vparty').
    # Take the first; record the key in `extra` for the consumer.
    key = next(iter(result))
    df = result[key]
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise VdemError(f"V-Dem {filename} -> {key} is not a usable DataFrame")

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
            "n_columns": len(df.columns),
            "description": desc,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
