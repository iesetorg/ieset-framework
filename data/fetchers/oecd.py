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
import re
import xml.etree.ElementTree as ET
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
    # Inferred from existing full-URN citations already used in the repo.
    "DSD_LFS": "OECD.SDD.TPS", "DSD_LFS_BS": "OECD.SDD.TPS",
    "DSD_EARNINGS": "OECD.SDD.TPS",
    "DSD_NAMAIN1": "OECD.SDD.NAD", "DSD_NAAG": "OECD.SDD.NAD",
}

_OECD_SHORTCUTS: dict[str, str] = {
    "EPL_OV": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
    "EPL_indicators": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
    "MWUSD": "OECD.ELS.SAE,DSD_EARN@DF_MW_DOL_RPP,1.0",
    "OUTGAP": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "OutputGap": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_KEI": "OECD.ECO.MAD,DSD_KEI@DF_KEI,1.0",
    "DSD_TAX": "OECD.CTP.TPS,DSD_TAX@DF_TAX_WAGES_COMP,2.1",
    "CPI:core": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
    "CPI": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
    "DSD_PRICES": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0",
    "DSD_PRICES@DF_PRICES_N_CP": "OECD.SDD.TPS,DSD_PRICES@DF_PRICES_N_CP,1.0",
    "DSD_TU@DF_TUD": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
    "DSD_TU@DF_CBC": "OECD.ELS.SAE,DSD_TUD_CBC@DF_CBC,1.0",
    "DSD_TU@DF_TU": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
    "TUD": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
    "trade_union_density": "OECD.ELS.SAE,DSD_TUD_CBC@DF_TUD,1.0",
    "HEALTH_STAT@DF_AMENABLE_MORT": "OECD.ELS.HD,DSD_HEALTH_STAT@DF_AMENABLE_MORT,1.0",
    "HOUSE_PRICES": "OECD.SDD.PIN,DSD_RHPI@DF_RHPI,1.0",
    "DSD_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "DSD_IDD@DF_IDD": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "DSD_IDD@DF_CHILD_POV": "OECD.WISE.INE,DSD_IDD@DF_CHILD_POV,1.0",
    "POVERTY": "OECD.WISE.INE,DSD_IDD@DF_IDD,1.0",
    "DSD_EARN": "OECD.ELS.SAE,DSD_EARN@DF_EARN_LFS,1.0",
    "DSD_EARNINGS": "OECD.SDD.TPS,DSD_EARNINGS@DF_EARNINGS,1.0",
    "NEET": "OECD.ELS.EMP,DSD_LFS@DF_NEET,1.0",
    "DSD_PDB": "OECD.SDD.TPS,DSD_PDB@DF_PDB_PT,1.0",
    "DSD_PENSIONS@DF_PENSIONS_REPL_RATE": "OECD.ELS.SAE,DSD_PENSIONS@DF_PENSIONS_REPL_RATE,1.0",
    "DSD_SOCX@DF_SOCX_AGG": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_AGG,1.0",
    "DSD_SOCX@DF_SOCX_ALMP": "OECD.ELS.SOC,DSD_SOCX@DF_SOCX_ALMP,1.0",
    "FDI_statistics": "OECD.DAF.INV,DSD_FDI@DF_FDI_FLOWS,1.0",
    "HFCE": "OECD.SDD.NAD,DSD_NAMAIN1@DF_HFCE,1.0",
    "Gov_Exp": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "GovExp": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "GGEXP": "OECD.SDD.NAD,DSD_NAMAIN1@DF_NAMAIN1_GFS,1.0",
    "STAN": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
    "STAN_VA": "OECD.SDD.TPS,DSD_STAN@DF_STAN,1.0",
}

_OECD_DATAFLOW_CACHE: list[dict[str, str | None]] | None = None


def _normalise_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _load_dataflows() -> list[dict[str, str | None]]:
    global _OECD_DATAFLOW_CACHE
    if _OECD_DATAFLOW_CACHE is not None:
        return _OECD_DATAFLOW_CACHE
    try:
        r = requests.get(
            "https://sdmx.oecd.org/public/rest/dataflow/all/all/latest",
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 IESET"},
        )
        r.raise_for_status()
        ns = {
            "s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
            "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
        }
        root = ET.fromstring(r.text)
        flows: list[dict[str, str | None]] = []
        for df in root.findall(".//s:Dataflow", ns):
            names = df.findall(".//c:Name", ns)
            name = next(
                (
                    n.text
                    for n in names
                    if n.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") == "en"
                ),
                names[0].text if names else "",
            )
            flows.append(
                {
                    "agencyID": df.attrib.get("agencyID"),
                    "id": df.attrib.get("id"),
                    "version": df.attrib.get("version") or "1.0",
                    "name": name,
                }
            )
        _OECD_DATAFLOW_CACHE = flows
    except Exception:
        _OECD_DATAFLOW_CACHE = []
    return _OECD_DATAFLOW_CACHE


def _resolve_by_catalogue(series_id: str) -> str | None:
    tokens = re.findall(r"(?:DSD|DF)_[A-Z0-9_]+", series_id.upper())
    if not tokens:
        return None
    norm_tokens = [_normalise_token(t) for t in tokens]
    best: tuple[int, dict[str, str | None]] | None = None
    for flow in _load_dataflows():
        haystack = _normalise_token(
            " ".join(str(flow.get(k) or "") for k in ("agencyID", "id", "name"))
        )
        score = sum(1 for token in norm_tokens if token and token in haystack)
        if score and (best is None or score > best[0]):
            best = (score, flow)
    if best is None:
        return None
    flow = best[1]
    agency = flow.get("agencyID")
    flow_id = flow.get("id")
    version = flow.get("version") or "1.0"
    if not agency or not flow_id:
        return None
    return f"{agency},{flow_id},{version}"


def _resolve_dataflow(series_id: str) -> str:
    """Convert partial OECD URN to full one. Already-full URNs pass through."""
    sid = series_id.strip()
    shortcut = _OECD_SHORTCUTS.get(sid) or _OECD_SHORTCUTS.get(sid.upper())
    if shortcut:
        return shortcut
    if sid in _OECD_SHORTCUTS:
        return _OECD_SHORTCUTS[sid]
    resolved = _resolve_by_catalogue(sid)
    if resolved:
        return resolved
    if sid.startswith("OECD.") and "," in sid:
        return sid
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
    # Older successful repo pulls used OECD's explicit `format=csvfilewithlabels`
    # URL shape; keep that transport contract instead of relying on content
    # negotiation, which has recently started returning 403s for some calls.
    params["format"] = "csvfilewithlabels"
    r = requests.get(
        url,
        params=params,
        timeout=120,
        headers={"User-Agent": "Mozilla/5.0 IESET"},
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
