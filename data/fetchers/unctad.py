"""UNCTAD (UN Conference on Trade and Development) fetcher.

Endpoint: https://unctadstat.unctad.org/EN/BulkDownload.html
Bulk CSVs:    https://unctadstat-api.unctad.org/bulkdownload/<DataflowID>/<Filename>
Auth: none. License: open (UN data terms — citation required).

UNCTADstat exposes a bulk-download portal that ships compressed (zip/7z) CSVs
of each headline dataset. The newer programmatic API (unctadstat-api) uses
the same dataflow IDs but returns SDMX-JSON for query-style calls. We take
the bulk-CSV path (simpler; the SDMX path is brittle and rate-limited).

Each entry in `SUPPORTED` maps a IESET-internal `series_id` to:
  - the UNCTADstat `dataflow_id` (used in the bulk URL)
  - a one-line description
  - a frequency hint
  - units string

The fetcher downloads the bulk zip, extracts the first CSV, parses with
pandas, normalises common column names, and emits a tidy long-form panel.

Currently supported series_ids:
  US.FDI               — FDI inward flows by economy and year (USD millions)
  US.FDIstock          — FDI inward stock by economy and year (USD millions)
  US.TradeMerchTotal   — Merchandise trade matrix (exports + imports, USD)
  US.TradeServ         — Trade in services by category (USD millions)
  US.GVCParticipation  — Global value chain participation indicators
"""
from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "UN data terms — open with citation"
METHODOLOGY_BASE = "https://unctadstat.unctad.org/EN/Classifications.html"

# Bulk-download host. UNCTADstat's bulk path is:
#   https://unctadstat-api.unctad.org/bulkdownload/<dataflow_id>/<filename>
# Filenames are always "<dataflow_id_with_underscores>" (dot replaced by
# underscore) without any extension when you append the filename only;
# the response is a zip containing a single CSV.
_BULK_HOST = "https://unctadstat-api.unctad.org/bulkdownload"

# Mirror via the legacy unctadstat.unctad.org domain (some dataflows live here).
_BULK_HOST_LEGACY = "https://unctadstat.unctad.org/7zip"


def _bulk_filename(dataflow_id: str) -> str:
    return dataflow_id.replace(".", "_")


SUPPORTED: dict[str, dict[str, Any]] = {
    "US.FDI": {
        "dataflow_id": "US.FdiFlowsStock",
        "desc": "FDI inward flows by economy (USD millions, annual)",
        "frequency": "annual",
        "units": "USD millions",
        "value_filter": {"FOI": "FI"},  # Flows-Inward in FdiFlowsStock dataflow
    },
    "US.FDIstock": {
        "dataflow_id": "US.FdiFlowsStock",
        "desc": "FDI inward stock by economy (USD millions, annual)",
        "frequency": "annual",
        "units": "USD millions",
        "value_filter": {"FOI": "SI"},  # Stocks-Inward
    },
    "US.TradeMerchTotal": {
        "dataflow_id": "US.TradeMatrix",
        "desc": "Merchandise trade — total exports + imports (USD, annual)",
        "frequency": "annual",
        "units": "USD",
        "value_filter": None,
    },
    "US.TradeServ": {
        "dataflow_id": "US.ServicesByCategory",
        "desc": "Trade in services by EBOPS category (USD millions, annual)",
        "frequency": "annual",
        "units": "USD millions",
        "value_filter": None,
    },
    "US.GVCParticipation": {
        "dataflow_id": "US.GVCParticipation",
        "desc": "Global value chain participation (forward + backward share, %)",
        "frequency": "annual",
        "units": "percent",
        "value_filter": None,
    },
}


class UnctadError(RuntimeError):
    pass


def _candidate_urls(dataflow_id: str) -> list[str]:
    fname = _bulk_filename(dataflow_id)
    return [
        # Primary: API host
        f"{_BULK_HOST}/{dataflow_id}/{fname}",
        f"{_BULK_HOST}/{dataflow_id}/{fname}.zip",
        # Legacy mirror
        f"{_BULK_HOST_LEGACY}/{fname}.7z",
        f"{_BULK_HOST_LEGACY}/{fname}.zip",
    ]


def _download_csv(dataflow_id: str) -> tuple[pd.DataFrame, str]:
    """Try candidate bulk URLs, return (DataFrame, source_url) or raise."""
    last_err: Exception | None = None
    headers = {"User-Agent": "Mozilla/5.0 ieset-fetcher"}
    for url in _candidate_urls(dataflow_id):
        try:
            r = requests.get(url, timeout=180, headers=headers)
        except requests.RequestException as e:
            last_err = e
            continue
        if r.status_code != 200 or not r.content:
            last_err = UnctadError(f"HTTP {r.status_code} for {url}")
            continue

        ctype = r.headers.get("Content-Type", "").lower()
        body = r.content
        # Try zip first (most common bulk wrapper)
        try:
            z = zipfile.ZipFile(io.BytesIO(body))
            csv_name = next(
                (n for n in z.namelist() if n.lower().endswith((".csv", ".txt"))),
                None,
            )
            if csv_name is None:
                raise UnctadError(f"no CSV inside zip from {url}: {z.namelist()}")
            with z.open(csv_name) as f:
                df = pd.read_csv(f, low_memory=False, encoding="latin-1", sep=None, engine="python")
            return df, url
        except zipfile.BadZipFile:
            pass

        # Maybe served as raw CSV
        if "csv" in ctype or body[:1] in (b'"', b"E", b"Y", b"C"):
            try:
                df = pd.read_csv(
                    io.BytesIO(body), low_memory=False, encoding="latin-1",
                    sep=None, engine="python",
                )
                return df, url
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
        last_err = UnctadError(f"unrecognised payload from {url} (ctype={ctype!r}, head={body[:40]!r})")

    raise UnctadError(f"all UNCTAD bulk URLs failed for {dataflow_id}: {last_err}")


def _normalise(df: pd.DataFrame, value_filter: dict | None) -> pd.DataFrame:
    """Normalise UNCTAD CSV to a long panel with columns: economy, year, value, ..."""
    df.columns = [str(c).strip() for c in df.columns]

    # Apply optional categorical filter (e.g. flows-inward only)
    if value_filter:
        for col, val in value_filter.items():
            if col in df.columns:
                df = df[df[col].astype(str) == val].copy()

    # UNCTAD CSVs typically use either a wide layout (year columns) or long
    # ("Period" / "Year" + "Value"). Detect and reshape if needed.
    year_cols = [c for c in df.columns if c.isdigit() and len(c) == 4]
    if year_cols and "Value" not in df.columns:
        id_vars = [c for c in df.columns if c not in year_cols]
        df = df.melt(id_vars=id_vars, value_vars=year_cols, var_name="year", value_name="value")
    else:
        # Long form already
        rename_map = {}
        for c in df.columns:
            cl = c.lower()
            if cl in ("period", "year", "time", "time_period"):
                rename_map[c] = "year"
            elif cl == "value" or cl.startswith("value"):
                rename_map[c] = "value"
        df = df.rename(columns=rename_map)

    # Best-effort economy/country column detection
    for cand in ("Economy_Label", "Economy", "ECONOMY", "Country", "Reporter", "Reporter_Label"):
        if cand in df.columns:
            df = df.rename(columns={cand: "economy"})
            break

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if "value" in df.columns:
        df = df.dropna(subset=["value"])
    if "year" in df.columns:
        df = df.dropna(subset=["year"])

    return df.reset_index(drop=True)


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: str | None = None,
) -> FetchResult:
    """Fetch a UNCTAD series by IESET series_id.

    series_id: one of the keys in SUPPORTED, e.g. 'US.FDI', 'US.TradeMerchTotal'.
    countries: optional ';'-separated ISO3 list to filter to (best-effort —
        depends on UNCTAD column naming for the dataflow).
    """
    if series_id not in SUPPORTED:
        raise UnctadError(
            f"unsupported UNCTAD series_id {series_id!r}; "
            f"known: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    dataflow_id = spec["dataflow_id"]

    fetch_ts = utc_now()
    raw, src_url = _download_csv(dataflow_id)
    df = _normalise(raw, spec.get("value_filter"))

    if df.empty:
        raise UnctadError(f"UNCTAD {series_id} returned no rows after normalisation")

    # Optional country filter (post-hoc, by matching ISO3 in the economy label)
    if countries:
        wanted = {c.strip().upper() for c in countries.split(";") if c.strip()}
        for col in ("economy", "Economy", "ISO3", "Country_Code"):
            if col in df.columns:
                mask = df[col].astype(str).str.upper().isin(wanted)
                if mask.any():
                    df = df[mask].reset_index(drop=True)
                    break

    path_out, sha = write_vintage(
        publisher="unctad",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "year" in df.columns and df["year"].notna().any():
        start = str(int(df["year"].min()))
        end = str(int(df["year"].max()))

    return FetchResult(
        publisher="unctad",
        series_id=series_id,
        source_url=src_url,
        methodology_url=f"https://unctadstat.unctad.org/EN/Index.html#{dataflow_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec.get("frequency", "annual"),
        units=spec.get("units", "per dataflow metadata"),
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "dataflow_id": dataflow_id,
            "desc": spec.get("desc"),
            "value_filter": spec.get("value_filter"),
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.fetchers import unctad as _self

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series", default="US.FDI", choices=sorted(SUPPORTED))
    p.add_argument("--countries", default=None)
    args = p.parse_args()
    res = _self.fetch(args.series, countries=args.countries)
    print(f"OK rows={res.rows} {res.start_date}->{res.end_date}")
    print(f"   {res.parquet_path}")
