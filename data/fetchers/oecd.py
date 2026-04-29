"""OECD SDMX 2.1 fetcher.

Endpoint: https://sdmx.oecd.org/public/rest/data
Docs:     https://data-explorer.oecd.org/vis?fs[0]=Topic ; dataflow catalogue
           https://sdmx.oecd.org/public/rest/dataflow/all/all/latest

OECD recently migrated from the legacy stats.oecd.org URL structure to the new
Data Explorer. Both still resolve but new queries should target the new base.

SDMX key format: dot-separated dimensions per the dataflow's DSD.
We fetch CSV (pandas-friendly) and preserve every dimension column.

Common dataflows used by IESET:
    OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0      (CPI harmonised)
    OECD.WISE.INE,DSD_WISE_IDD@DF_IDD,1.0           (Income Distribution Database — Gini)
    OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0           (Employment Protection Legislation)
    OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0                 (Key Economic Indicators — share prices, etc.)

License: OECD standard permissions (attribution).
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

OECD_BASE = "https://sdmx.oecd.org/public/rest/data"
LICENSE = "OECD standard permissions (attribution required)"

_DSD_AGENCY: dict[str, str] = {
    "DSD_PRICES": "OECD.SDD.TPS", "DSD_PDB": "OECD.SDD.TPS",
    "DSD_KEI": "OECD.ECO.MAD", "DSD_EARN": "OECD.ELS.SAE",
    "DSD_TU": "OECD.ELS.SAE", "DSD_LMS": "OECD.ELS.EMP",
    "DSD_EPL_OV": "OECD.ELS.EMP", "DSD_PENSIONS": "OECD.ELS.SAE",
    "DSD_UBR": "OECD.ELS.SAE", "DSD_SOCX": "OECD.ELS.SOC",
    "DSD_IDD": "OECD.WISE.INE", "DSD_WISE_IDD": "OECD.WISE.INE",
    "DSD_TAX": "OECD.CTP.TPS", "DSD_TAX_WAGES_COMP": "OECD.CTP.TPS",
    "DSD_TAX_CIT": "OECD.CTP.TPS", "DSD_HEALTH_STAT": "OECD.ELS.HD",
    "DSD_PMR": "OECD.ECO.GCRD", "DSD_MIG": "OECD.ELS.IMD",
    "DSD_DASHBOARD": "OECD.CFE.RDG",
}

_OECD_SHORTCUTS: dict[str, str] = {
    "EPL_OV": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
    "MWUSD": "OECD.ELS.SAE,DSD_EARN@DF_MW_DOL_RPP,1.0",
    "OUTGAP": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_KEI": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_TAX": "OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1",
    "CPI:core": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
    "CPI": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
}


def _resolve_dataflow(series_id: str) -> str:
    """Convert partial OECD URN to full one. Already-full URNs pass through."""
    sid = series_id.strip()
    if sid.startswith("OECD.") and "," in sid:
        return sid
    if sid in _OECD_SHORTCUTS:
        return _OECD_SHORTCUTS[sid]
    head = sid.split("@", 1)[0]
    if head in _DSD_AGENCY:
        agency = _DSD_AGENCY[head]
        if "@" not in sid:
            df = sid.replace("DSD_", "DF_") if sid.startswith("DSD_") else sid
            return f"{agency},{sid}@{df},1.0"
        return f"{agency},{sid},1.0"
    return sid


class OecdError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    key: str = "",
    start_period: str | None = None,
    end_period: str | None = None,
    publisher_id: str = "oecd",
) -> FetchResult:
    """Fetch an OECD dataflow.

    series_id: full SDMX dataflow identifier,
               e.g., 'OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0'
    key:       dot-separated SDMX key filter (empty = all dimensions).
    start_period / end_period: optional period bounds, e.g., '2008-01', '2025-12'.
    publisher_id: override for FetchResult.publisher + vintage path. Used by
                  thin wrappers (oecd_pmr, etc.) to namespace their data
                  while reusing this fetcher. Defaults to 'oecd'.
    """
    fetch_ts = utc_now()
    params: dict[str, str] = {}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    resolved = _resolve_dataflow(series_id)
    url = f"{OECD_BASE}/{resolved}/{key or 'all'}"
    r = requests.get(
        url,
        params=params,
        timeout=120,
        headers={"Accept": "application/vnd.sdmx.data+csv;version=1.0"},
    )
    if r.status_code == 404:
        raise OecdError(f"OECD 404 for {series_id} (resolved='{resolved}') key='{key}' — check dataflow id")
    r.raise_for_status()
    text = r.text
    if not text.strip():
        raise OecdError(f"OECD returned empty CSV for {series_id}")
    df = pd.read_csv(io.StringIO(text), low_memory=False)

    # Standardise common columns
    if "TIME_PERIOD" in df.columns:
        df = df.rename(columns={"TIME_PERIOD": "period"})
    if "OBS_VALUE" in df.columns:
        df = df.rename(columns={"OBS_VALUE": "value"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher=publisher_id,
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = str(df["period"].min()) if "period" in df.columns and len(df) else None
    end = str(df["period"].max()) if "period" in df.columns and len(df) else None

    return FetchResult(
        publisher=publisher_id,
        series_id=series_id,
        source_url=f"{url}?format=csvfilewithlabels",
        methodology_url=f"https://data-explorer.oecd.org/vis?fs[0]=Topic&df[ds]=dsDisseminateFinalDMZ&df[id]={series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_infer_frequency(df),
        units="per dataflow metadata",
        currency=None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "sdmx_key": key or "(all)",
            "start_period": start_period,
            "end_period": end_period,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _infer_frequency(df: pd.DataFrame) -> str:
    freq_col = next((c for c in ("FREQ", "FREQUENCY") if c in df.columns), None)
    if freq_col is None:
        return "unknown"
    unique = df[freq_col].dropna().unique().tolist()
    if len(unique) != 1:
        return "mixed"
    return {"A": "annual", "Q": "quarterly", "M": "monthly", "D": "daily"}.get(
        str(unique[0]), str(unique[0])
    )
