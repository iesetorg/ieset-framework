"""World Bank WITS / UNCTAD TRAINS fetcher.

Uses WITS' documented JSON API for trade and tariff indicators where possible,
with World Bank WDI mirrors for WIPO/WDI-style trade indicators that WITS does
not expose through the trade-stats datasource. Stored vintages are namespaced
under ``wits``; ``publishers.yaml`` aliases ``world_bank_wits`` to this fetcher.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as robust_get

LICENSE = "World Bank WITS terms / World Bank API CC-BY where mirrored"
WITS_BASE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource"
WB_BASE = "https://api.worldbank.org/v2"

WITS_INDICATORS: dict[str, dict[str, str]] = {
    "product_concentration": {
        "indicator": "HH-MKT-CNCNTRTN-NDX",
        "datasource": "tradestats-trade",
        "partner": "",
        "product": "",
        "units": "0-1 HHI-style concentration index",
        "desc": "WITS export market/product concentration index",
    },
    "unique_hs6_products": {
        "indicator": "NMBR-XPRT-HS6-PRDCT",
        "datasource": "tradestats-trade",
        "partner": "wld",
        "product": "",
        "units": "count",
        "desc": "Number of exported HS6 products",
    },
    "product_lines": {
        "indicator": "NMBR-MPRT-HS6-PRDCT",
        "datasource": "tradestats-trade",
        "partner": "wld",
        "product": "",
        "units": "count",
        "desc": "Number of imported HS6 products",
    },
}

WB_INDICATORS: dict[str, dict[str, str]] = {
    "import_value": {
        "indicator": "TM.VAL.MRCH.CD.WT",
        "units": "current USD",
        "desc": "Merchandise imports, current USD, World Bank/WITS compatible mirror",
    },
    "export_value_constant_usd": {
        "indicator": "TX.VAL.MRCH.CD.WT",
        "units": "current USD",
        "desc": "Merchandise exports, current USD, World Bank/WITS compatible mirror",
    },
    "tariff_average": {
        "indicator": "TM.TAX.MRCH.WM.AR.ZS",
        "units": "percent",
        "desc": "Tariff rate, applied, weighted mean, all products",
    },
    "weighted_mean_applied_tariff": {
        "indicator": "TM.TAX.MRCH.WM.AR.ZS",
        "units": "percent",
        "desc": "Tariff rate, applied, weighted mean, all products",
    },
    "high_tech_exports": {
        "indicator": "TX.VAL.TECH.CD",
        "units": "current USD",
        "desc": "High-technology exports, current USD; WDI/WITS-compatible mirror",
    },
}


class WitsError(RuntimeError):
    pass


def _years_arg(start_year: int, end_year: int) -> str:
    return ";".join(str(y) for y in range(start_year, end_year + 1))


def _flatten_dicts(obj: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if len(obj) >= 3 and any(k.lower() in {"value", "obs_value"} for k in obj):
            rows.append(obj)
        for value in obj.values():
            rows.extend(_flatten_dicts(value))
    elif isinstance(obj, list):
        for item in obj:
            rows.extend(_flatten_dicts(item))
    return rows


def _normalise_wits_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.columns = [str(c).strip() for c in df.columns]

    rename: dict[str, str] = {}
    for col in df.columns:
        key = re.sub(r"[^a-z0-9]+", "_", col.lower()).strip("_")
        if key in {"reporter", "reporteriso3", "reporter_iso3", "reporter_code"}:
            rename[col] = "country_iso3"
        elif key in {"reporter_name", "reportername"}:
            rename[col] = "country_name"
        elif key in {"time_period", "year", "period"}:
            rename[col] = "year"
        elif key in {"obs_value", "value", "trade_value"}:
            rename[col] = "value"
        elif key in {"indicator", "indicator_code"}:
            rename[col] = "indicator_id"
        elif key in {"partner", "partneriso3", "partner_iso3", "partner_code"}:
            rename[col] = "partner_iso3"
        elif key in {"product", "productcode", "product_code"}:
            rename[col] = "product_code"
    df = df.rename(columns=rename)

    if "country_iso3" not in df.columns:
        for col in df.columns:
            if df[col].astype(str).str.fullmatch(r"[A-Z]{3}").mean() > 0.5:
                df = df.rename(columns={col: "country_iso3"})
                break
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if "country_iso3" in df.columns:
        df["country_iso3"] = df["country_iso3"].astype("string").str.upper()
    if "value" in df.columns:
        df = df.dropna(subset=["value"])
    if "year" in df.columns:
        df = df.dropna(subset=["year"])
    if "country_iso3" in df.columns and "year" in df.columns:
        df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    return df


def _parse_sdmx_json(data: dict[str, Any]) -> pd.DataFrame:
    structure = data.get("structure") or {}
    dims = structure.get("dimensions") or {}
    series_dims = dims.get("series") or []
    obs_dims = dims.get("observation") or []
    datasets = data.get("dataSets") or []
    if not datasets:
        return pd.DataFrame()
    dataset = datasets[0]
    series_block = dataset.get("series") or {}
    if not series_block:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for series_key, payload in series_block.items():
        indexes = [int(part) for part in str(series_key).split(":") if part != ""]
        base: dict[str, Any] = {}
        for dim, idx in zip(series_dims, indexes):
            values = dim.get("values") or []
            value = values[idx] if idx < len(values) else {}
            dim_id = str(dim.get("id") or "").lower()
            base[f"{dim_id}_id"] = value.get("id")
            base[f"{dim_id}_name"] = value.get("name")
        for obs_key, obs in (payload.get("observations") or {}).items():
            row = dict(base)
            obs_indexes = [int(part) for part in str(obs_key).split(":") if part != ""]
            for dim, idx in zip(obs_dims, obs_indexes):
                values = dim.get("values") or []
                value = values[idx] if idx < len(values) else {}
                if (dim.get("id") or "").upper() == "TIME_PERIOD":
                    row["year"] = value.get("id")
                else:
                    row[str(dim.get("id") or "").lower()] = value.get("id")
            row["value"] = obs[0] if isinstance(obs, list) and obs else obs
            rows.append(row)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    rename = {
        "reporter_id": "country_iso3",
        "reporter_name": "country_name",
        "partner_id": "partner_iso3",
        "partner_name": "partner_name",
        "productcode_id": "product_code",
        "productcode_name": "product_name",
        "indicator_id": "indicator_id",
        "indicator_name": "indicator_name",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "country_iso3" in df.columns:
        df["country_iso3"] = df["country_iso3"].astype("string").str.upper()
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    if {"country_iso3", "year"}.issubset(df.columns):
        df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    return df


def _fetch_wits_indicator(series_id: str, spec: dict[str, str], start_year: int, end_year: int) -> tuple[pd.DataFrame, str]:
    years = "all" if start_year <= 1988 and end_year >= 2023 else _years_arg(start_year, end_year)
    reporter = "all"
    datasource = spec.get("datasource", "tradestats-trade")
    parts = [f"{WITS_BASE}/{datasource}", f"reporter/{reporter}", f"year/{years}"]
    if spec.get("partner"):
        parts.append(f"partner/{spec['partner']}")
    if spec.get("product"):
        parts.append(f"product/{spec['product']}")
    parts.append(f"indicator/{spec['indicator']}")
    url = "/".join(parts)
    payload = robust_get(url, params={"format": "JSON"}, timeout=240, return_http_errors=True)
    if payload.status_code >= 400:
        raise WitsError(f"WITS HTTP {payload.status_code} for {series_id} via {payload.transport}")
    try:
        data = json.loads(payload.text)
    except json.JSONDecodeError as exc:
        raise WitsError(f"WITS returned non-JSON for {series_id}: {payload.text[:240]!r}") from exc
    df = _parse_sdmx_json(data)
    if df.empty:
        df = _normalise_wits_rows(_flatten_dicts(data))
    if df.empty:
        raise WitsError(f"WITS returned no rows for {series_id} ({spec['indicator']})")
    if "indicator_id" not in df.columns:
        df["indicator_id"] = spec["indicator"]
    df["series_id"] = series_id
    return df, payload.transport


def _iter_wb_pages(indicator: str, countries: str) -> list[dict[str, Any]]:
    page = 1
    rows: list[dict[str, Any]] = []
    while True:
        payload = robust_get(
            f"{WB_BASE}/country/{countries}/indicator/{indicator}",
            params={"format": "json", "per_page": "20000", "page": str(page)},
            timeout=180,
        )
        data = json.loads(payload.text)
        if not isinstance(data, list) or len(data) < 2:
            raise WitsError(f"World Bank mirror error for {indicator}: {data}")
        meta, page_rows = data
        if not page_rows:
            break
        rows.extend(page_rows)
        if page >= int(meta.get("pages", 1)):
            break
        page += 1
    return rows


def _fetch_wb_indicator(series_id: str, spec: dict[str, str], countries: str) -> tuple[pd.DataFrame, str]:
    rows = _iter_wb_pages(spec["indicator"], countries)
    if not rows:
        raise WitsError(f"World Bank mirror returned no rows for {series_id}")
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
    df["country_iso3"] = df["countryiso3code"]
    df["country_name"] = df["country"].apply(lambda c: c.get("value") if isinstance(c, dict) else None)
    df["indicator_id"] = spec["indicator"]
    df["series_id"] = series_id
    df = (
        df[["country_iso3", "country_name", "indicator_id", "series_id", "year", "value", "unit", "obs_status", "decimal"]]
        .dropna(subset=["country_iso3", "year"])
        .sort_values(["country_iso3", "year"])
        .reset_index(drop=True)
    )
    return df, "world_bank_wdi_mirror"


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: str = "all",
    start_year: int = 1988,
    end_year: int = 2024,
) -> FetchResult:
    fetch_ts = utc_now()
    transport = "unknown"
    if series_id in WITS_INDICATORS:
        spec = WITS_INDICATORS[series_id]
        df, transport = _fetch_wits_indicator(series_id, spec, start_year, end_year)
        source_url = f"{WITS_BASE}/{spec.get('datasource', 'tradestats-trade')}/reporter/all/year/{start_year}-{end_year}/indicator/{spec['indicator']}"
        methodology_url = "https://wits.worldbank.org/witsapiintro.aspx?lang=en"
    elif series_id in WB_INDICATORS:
        spec = WB_INDICATORS[series_id]
        df, transport = _fetch_wb_indicator(series_id, spec, countries)
        source_url = f"{WB_BASE}/country/{countries}/indicator/{spec['indicator']}?format=json"
        methodology_url = f"https://data.worldbank.org/indicator/{spec['indicator']}"
    else:
        raise WitsError(
            f"unsupported WITS series_id {series_id!r}; "
            f"known: {sorted(set(WITS_INDICATORS) | set(WB_INDICATORS))}"
        )

    path, sha = write_vintage(
        publisher="wits",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )
    start = str(int(df["year"].min())) if "year" in df.columns and df["year"].notna().any() else None
    end = str(int(df["year"].max())) if "year" in df.columns and df["year"].notna().any() else None

    return FetchResult(
        publisher="wits",
        series_id=series_id,
        source_url=source_url,
        methodology_url=methodology_url,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=spec.get("units", "per WITS metadata"),
        currency="USD" if "value" in series_id else None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=path,
        extra={
            "desc": spec.get("desc"),
            "transport": transport,
            "countries_param": countries,
            "start_year": start_year,
            "end_year": end_year,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
            "columns": list(df.columns),
        },
    )
