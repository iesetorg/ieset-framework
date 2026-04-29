"""European Central Bank Statistical Data Warehouse (SDMX 2.1) fetcher.

Endpoint: https://data-api.ecb.europa.eu/service
Auth: none. License: ECB standard terms (attribution required).

Key format: '<flow_ref>/<key>?format=csvdata' where key is dot-separated
SDMX dimension values. Use '' for wildcard within a position.

Common flow_refs:
    BSI    Balance Sheet Items (money aggregates M1/M2/M3 + components)
    MIR    MFI interest rates
    EXR    Bilateral exchange rates
    FM     Financial markets (money market rates, yields)
    YC     Government bond yield curve

Euro-area M3 (the ECB's preferred aggregate; M2 available via M20 component):
    BSI/M.U2.Y.V.M30.X.I.U2.2300.Z01.A    Annual growth rate, monthly

National contributions to euro-area aggregates require country-specific keys
(e.g. REF_AREA=DE); resolve per-country at hypothesis-wiring time against
the live constraint set.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

BASE = "https://data-api.ecb.europa.eu/service"
LICENSE = "oecd_terms"

_ECB_SHORTCUTS: dict[str, tuple[str, str]] = {
    "FM": ("FM", "M.U2.EUR.4F.KR.MRR_FR.LEV"),
    "FM:STN": ("FM", "M.U2.EUR.4F.KR.MRR_FR.LEV"),
    "FM.M.U2.EUR.4F.KR.MRR_FR.LEV": ("FM", "M.U2.EUR.4F.KR.MRR_FR.LEV"),
    "financial_markets_money_market_OIS": ("FM", "M.U2.EUR.4F.MM.EONIA_.HSTA"),
    "euribor": ("FM", "M.U2.EUR.RT.MM.EURIBOR3MD_.HSTA"),
    "financial_markets_yields_2yr": ("FM", "M.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y"),
    "financial_markets_yields_5yr": ("FM", "M.U2.EUR.4F.G_N_A.SV_C_YM.SR_5Y"),
    "financial_markets_yields_10yr": ("FM", "M.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y"),
    "financial_markets_inflation_linked_swaps": ("FM", "M.I8.EUR.RT.MM.EONIA_.HSTA"),
    "EXR.D.GBP.EUR": ("EXR", "D.GBP.EUR.SP00.A"),
    "ICP": ("ICP", "M.U2.N.000000.4.ANR"),
    "IRS": ("MIR", "M.U2.B.A2A.A.R.A.2240.EUR.N"),
    "IRS.M.DE": ("MIR", "M.DE.B.A2A.A.R.A.2240.EUR.N"),
    "ILM": ("ILM", "W.U2.C.LT00.Z5.Z01.E"),
    "EMBI": ("FM", "D.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y"),
    "EMBI series": ("FM", "D.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y"),
}


def _resolve_flow_key(series_id: str, override_key: str) -> tuple[str, str]:
    sid = series_id.strip()
    if sid in _ECB_SHORTCUTS:
        flow, default_key = _ECB_SHORTCUTS[sid]
        return flow, override_key or default_key
    if "/" in sid:
        flow, _, k = sid.partition("/")
        return flow, override_key or k
    head = sid.split(".", 1)[0]
    if head in {"BSI", "MIR", "EXR", "FM", "YC", "ICP", "ILM", "STS", "QSA", "BPS"}:
        if head == sid:
            return head, override_key
        return head, override_key or sid[len(head) + 1:]
    return sid, override_key


class EcbError(RuntimeError):
    pass


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    key: str = "",
    start_period: str | None = None,
    end_period: str | None = None,
) -> FetchResult:
    """series_id: ECB flow OR 'flow/key' OR a registered shortcut name.
    key: optional dot-separated SDMX key; overrides shortcut default.
    """
    fetch_ts = utc_now()
    flow, resolved_key = _resolve_flow_key(series_id, key)
    series_id = flow
    key = resolved_key
    path = key or ""
    url = f"{BASE}/data/{series_id}/{path}"
    params = {"format": "csvdata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    r = requests.get(url, params=params, timeout=120, headers={"Accept": "text/csv"})
    if r.status_code == 404:
        raise EcbError(f"ECB 404 for {series_id}/{path} — check flow + key format")
    r.raise_for_status()
    text = r.text
    if not text.strip():
        raise EcbError(f"ECB returned empty CSV for {series_id}/{path}")
    df = pd.read_csv(io.StringIO(text), low_memory=False)
    if "TIME_PERIOD" in df.columns:
        df = df.rename(columns={"TIME_PERIOD": "period"})
    if "OBS_VALUE" in df.columns:
        df = df.rename(columns={"OBS_VALUE": "value"})
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Series_id for storage = flow_ref + optional key suffix so vintages are
    # disambiguated when different keys are pulled from the same flow.
    storage_id = f"{series_id}__{key}" if key else series_id
    path_out, sha = write_vintage(
        publisher="ecb",
        series_id=storage_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="ecb",
        series_id=storage_id,
        source_url=f"{url}?format=csvdata",
        methodology_url=f"https://data.ecb.europa.eu/search-results?searchTerm={series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=_infer_frequency(df),
        units="per flow metadata",
        currency="EUR",
        start_date=str(df["period"].min()) if "period" in df.columns and len(df) else None,
        end_date=str(df["period"].max()) if "period" in df.columns and len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "flow_ref": series_id,
            "sdmx_key": key or "(all)",
            "start_period": start_period,
            "end_period": end_period,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


def _infer_frequency(df: pd.DataFrame) -> str:
    if "FREQ" in df.columns:
        freqs = df["FREQ"].dropna().unique().tolist()
        if len(freqs) == 1:
            return {"A": "annual", "Q": "quarterly", "M": "monthly", "D": "daily"}.get(freqs[0], str(freqs[0]))
    return "unknown"
