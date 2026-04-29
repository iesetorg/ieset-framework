"""BIS Statistics fetcher.

Targets the BIS SDMX 2.1 API:
    https://stats.bis.org/api/v2/data/<dataflow>/<key>?format=csv

Core datasets used by IESET hypotheses:
    WS_SPP (Selected residential property prices) — quarterly real + nominal
    WS_LONG_PP (Long series, real residential property prices) — annual, 1970-
    WS_EER (Effective exchange rates) — monthly narrow + broad NEER/REER
    WS_TC_LONG (Long credit series) — quarterly, total credit to private sector

License: BIS Statistical Bulletin public-use terms; citation required.

The SDMX key format is dot-separated dimensions; the public catalogue documents
each dataflow's dimension order. For robustness we ask for the full dataflow
(empty dimensions = all) and filter client-side. This trades bandwidth for
schema resilience — BIS occasionally adds dimensions.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BIS_BASE = "https://stats.bis.org/api/v2"
LICENSE = "BIS Statistical Bulletin (public-use; attribution required)"

# Canonical BIS dataflows (verified against
# https://stats.bis.org/api/v2/structure/dataflow/BIS/all/latest on 2026-04).
DATAFLOWS = {
    "WS_SPP":         "Selected residential property prices (quarterly; includes long series)",
    "WS_CPP":         "Commercial property prices (where available)",
    "WS_EER":         "Effective exchange rates (monthly, NEER + REER, narrow + broad)",
    "WS_XRU":         "US-dollar exchange rates (daily/monthly)",
    "WS_TC":          "Total credit to non-financial sector (quarterly)",
    "WS_CREDIT_GAP":  "Credit-to-GDP gap (quarterly)",
    "WS_DSR":         "Debt service ratios for the private non-financial sector (quarterly)",
    "WS_LONG_CPI":    "Long consumer price inflation series (annual, 1800s-)",
    "WS_CBPOL":       "Central bank policy rates",
    "WS_DPP":         "Domestic property prices (where applicable)",
}


class BisError(RuntimeError):
    pass


def _request_csv(dataflow: str, key: str = "") -> pd.DataFrame:
    # BIS accepts empty key with a trailing slash; `all` returns 404 here
    # (unlike OECD's SDMX implementation). Empirically verified 2026-04.
    url = f"{BIS_BASE}/data/dataflow/BIS/{dataflow}/1.0/{key}"
    r = requests.get(url, params={"format": "csv"}, timeout=180)
    r.raise_for_status()
    text = r.text
    if not text.strip():
        raise BisError(f"BIS returned empty CSV for {dataflow}/{key}")
    return pd.read_csv(io.StringIO(text), low_memory=False)


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    key: str = "",
) -> FetchResult:
    """Fetch a BIS dataflow.

    series_id: dataflow name (e.g., 'WS_SPP', 'WS_LONG_PP', 'WS_EER').
    key:       optional SDMX dot-path filter. Empty → whole dataflow.
    """
    if series_id not in DATAFLOWS:
        # Not fatal — BIS has many dataflows. Just note it's not in our catalogue.
        pass

    fetch_ts = utc_now()
    df = _request_csv(series_id, key)

    # Normalise columns. BIS SDMX CSV headers include TIME_PERIOD, OBS_VALUE,
    # and dataflow-specific dimension columns. Preserve everything; promote the
    # standard names.
    rename_map = {"TIME_PERIOD": "period", "OBS_VALUE": "value"}
    df = df.rename(columns=rename_map)
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    path_out, sha = write_vintage(
        publisher="bis",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = str(df["period"].min()) if "period" in df.columns and len(df) else None
    end = str(df["period"].max()) if "period" in df.columns and len(df) else None

    return FetchResult(
        publisher="bis",
        series_id=series_id,
        source_url=f"{BIS_BASE}/data/dataflow/BIS/{series_id}/1.0/{key}?format=csv",
        methodology_url=f"https://data.bis.org/topics/{series_id}",
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
            "dataflow_description": DATAFLOWS.get(series_id, "(not in local catalogue)"),
            "sdmx_key": key or "(all)",
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _infer_frequency(df: pd.DataFrame) -> str:
    if "FREQ" in df.columns:
        unique = df["FREQ"].dropna().unique().tolist()
        if len(unique) == 1:
            return {"A": "annual", "Q": "quarterly", "M": "monthly", "D": "daily"}.get(
                unique[0], str(unique[0])
            )
        return "mixed"
    return "unknown"
