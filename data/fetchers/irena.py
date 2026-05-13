"""IRENA (International Renewable Energy Agency) fetcher.

Source: https://www.irena.org/Data
PxWeb (PC-Axis) JSON-stat 2.0 API:
    https://pxweb.irena.org/api/v1/en/IRENASTAT/<area>/<table>.px

Auth: none. License: IRENA terms — "free for use with attribution"; treated
as `unknown` per IESET's publishers schema (no canonical CC mapping
documented at the time of writing).

IRENA's primary publications:
  - Renewable Capacity Statistics (annual; installed MW by country, year,
    technology). PxWeb table family: ELECCAP / RECAP.
  - Renewable Power Generation Costs (annual report; LCOE by technology).
    LCOE series are published as CSV/Excel companions to the annual report;
    no stable PxWeb table for LCOE — manual-drop fallback expected.

Strategy:
  1. For installed-capacity series, POST a curated JSON query to the PxWeb
     endpoint (PxWeb returns JSON-stat which we flatten to a long panel).
  2. For LCOE series (and any PxWeb failure), fall back to a manual-drop
     under data/manual/irena/ — the user places the latest IRENA bulk
     XLSX/CSV there and the fetcher parses the first sheet/file.

Currently supported series_ids:
  installed_capacity_renewable  — total renewable capacity by country/year (MW)
  installed_capacity_solar_pv   — solar PV installed capacity (MW)
  installed_capacity_wind       — wind installed capacity (MW, on+offshore)
  lcoe_solar_pv                 — LCOE solar PV (USD/MWh) [manual-drop]
  lcoe_wind_onshore             — LCOE onshore wind (USD/MWh) [manual-drop]
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as robust_get
from ._manual_utils import find_latest, ManualDropError

LICENSE = "unknown"  # IRENA terms: free for use with attribution
METHODOLOGY = "https://www.irena.org/Publications"

PXWEB_BASE = "https://pxweb.irena.org/api/v1/en/IRENASTAT/Power Capacity and Generation"

# Default PxWeb table; cycle suffix bumps annually. We try the latest known
# cycle first and fall back to a couple of prior cycles if 404'd.
_PXWEB_CAPACITY_TABLES = [
    "Country_ELECCAP_2026_H1_v-PX 1.px",
    "Country_ELECCAP_2025_H2_v-PX 1.px",
    "Country_ELECCAP_2025_H1_v-PX 1.px",
    "Country_ELECSTAT_2025_H2_PX.px",
]


SUPPORTED: dict[str, dict[str, Any]] = {
    "installed_capacity_renewable": {
        "source": "pxweb",
        "table_candidates": _PXWEB_CAPACITY_TABLES,
        "tech_filter": ["total renewable", "renewable energy"],
        "desc": "Total renewable installed capacity by country/year (MW)",
        "frequency": "annual",
        "units": "MW",
    },
    "installed_capacity_solar_pv": {
        "source": "pxweb",
        "table_candidates": _PXWEB_CAPACITY_TABLES,
        "tech_filter": ["Solar photovoltaic", "Solar PV"],
        "desc": "Solar PV installed capacity by country/year (MW)",
        "frequency": "annual",
        "units": "MW",
    },
    "installed_capacity_wind": {
        "source": "pxweb",
        "table_candidates": _PXWEB_CAPACITY_TABLES,
        "tech_filter": ["Wind", "Onshore wind energy", "Offshore wind energy"],
        "desc": "Wind installed capacity by country/year (MW; on+offshore)",
        "frequency": "annual",
        "units": "MW",
    },
    "lcoe_solar_pv": {
        "source": "manual",
        "manual_hint": "solar",
        "desc": "Levelised cost of electricity, solar PV (USD/MWh)",
        "frequency": "annual",
        "units": "USD/MWh",
    },
    "lcoe_wind_onshore": {
        "source": "manual",
        "manual_hint": "wind",
        "desc": "Levelised cost of electricity, onshore wind (USD/MWh)",
        "frequency": "annual",
        "units": "USD/MWh",
    },
}

SERIES_ALIASES = {
    "capacity": "installed_capacity_renewable",
    "solar_pv_costs": "lcoe_solar_pv",
    "wind_lcoe": "lcoe_wind_onshore",
}


class IrenaError(RuntimeError):
    pass


# ----------------------------------------------------------------------
# PxWeb path
# ----------------------------------------------------------------------

def _pxweb_metadata(table: str) -> dict:
    url = f"{PXWEB_BASE}/{table}"
    payload = robust_get(url, timeout=60, headers={"Accept": "application/json,*/*;q=0.8"})
    return json.loads(payload.text)


def _pxweb_query(table: str, body: dict) -> dict:
    url = f"{PXWEB_BASE}/{table}"
    r = requests.post(
        url,
        json=body,
        timeout=180,
        headers={
            "User-Agent": "ieset-fetcher",
            "Content-Type": "application/json",
        },
    )
    r.raise_for_status()
    return r.json()


def _query_all(table: str) -> dict:
    """Build a 'select all' PxWeb query that asks for every dimension value
    in JSON-stat 2.0 format."""
    meta = _pxweb_metadata(table)
    queries = []
    for var in meta.get("variables", []) or []:
        code = var.get("code")
        values = var.get("values") or []
        if not code or not values:
            continue
        queries.append({
            "code": code,
            "selection": {"filter": "item", "values": values},
        })
    body = {"query": queries, "response": {"format": "json-stat2"}}
    return _pxweb_query(table, body)


def _values_matching(var: dict, needles: list[str]) -> list[str]:
    values = var.get("values") or []
    labels = var.get("valueTexts") or values
    out: list[str] = []
    for code, label in zip(values, labels):
        haystack = f"{code} {label}".lower()
        if any(needle.lower() in haystack for needle in needles):
            out.append(code)
    return out


def _query_capacity(table: str, tech_filter: list[str] | None) -> dict:
    """Build a filtered PxWeb query below IRENA's 100k-cell limit."""
    meta = _pxweb_metadata(table)
    queries = []
    for var in meta.get("variables", []) or []:
        code = var.get("code")
        values = var.get("values") or []
        if not code or not values:
            continue
        code_l = code.lower()
        selection = list(values)
        if "technology" in code_l and tech_filter:
            selection = _values_matching(var, tech_filter)
        elif "grid" in code_l:
            total = _values_matching(var, ["total", "all"])
            if total:
                selection = total[:1]
        elif "data type" in code_l or code_l in ("datatype", "data_type"):
            capacity = _values_matching(var, ["capacity"])
            if capacity:
                selection = capacity
        if not selection:
            raise IrenaError(f"no matching values for dimension {code!r} in {table}")
        queries.append({
            "code": code,
            "selection": {"filter": "item", "values": selection},
        })
    body = {"query": queries, "response": {"format": "json-stat2"}}
    return _pxweb_query(table, body)


def _jsonstat_to_long(payload: dict) -> pd.DataFrame:
    """Flatten a JSON-stat 2.0 response into a long DataFrame.

    Each row carries one observation plus the labels of every dimension.
    """
    dims = payload.get("id") or []
    sizes = payload.get("size") or []
    dim_meta = payload.get("dimension") or {}
    values = payload.get("value") or []

    # Build per-dimension ordered category-label arrays.
    cat_codes: list[list[str]] = []
    cat_labels: list[list[str]] = []
    for d in dims:
        cat = dim_meta.get(d, {}).get("category", {})
        idx = cat.get("index", {})
        lbl = cat.get("label", {}) or {}
        # idx may be a dict {code: position} or a list of codes
        if isinstance(idx, dict):
            ordered = sorted(idx.items(), key=lambda kv: kv[1])
            codes = [k for k, _ in ordered]
        elif isinstance(idx, list):
            codes = list(idx)
        else:
            codes = []
        cat_codes.append(codes)
        cat_labels.append([lbl.get(c, c) for c in codes])

    rows: list[dict] = []
    if isinstance(values, dict):
        # Sparse representation: keys are flat indices as strings.
        items = ((int(k), v) for k, v in values.items())
    else:
        items = enumerate(values)

    # Pre-compute strides for unraveling flat index.
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    for flat_idx, val in items:
        if val is None:
            continue
        coords = []
        rem = flat_idx
        for s in strides:
            coords.append(rem // s)
            rem = rem % s
        row: dict[str, Any] = {}
        for d, c, codes, labels in zip(dims, coords, cat_codes, cat_labels):
            if d.lower() in ("country/area", "region/country/area"):
                row[d] = codes[c] if 0 <= c < len(codes) else None
            else:
                row[d] = labels[c] if 0 <= c < len(labels) else None
        row["value"] = val
        rows.append(row)

    return pd.DataFrame(rows)


def _normalise_capacity(df: pd.DataFrame, tech_filter: list[str] | None) -> pd.DataFrame:
    # Standardise column names where possible.
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("country", "region", "country/area", "country_area", "region/country/area"):
            rename[c] = "country"
        elif cl in ("year", "time", "period"):
            rename[c] = "year"
        elif cl in ("technology", "ren_tech", "energy_technology", "tech"):
            rename[c] = "technology"
        elif cl in ("indicator", "data_type"):
            rename[c] = "indicator"
    df = df.rename(columns=rename)

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    if tech_filter and "technology" in df.columns:
        wanted = {t.lower() for t in tech_filter}
        mask = df["technology"].astype(str).str.lower().apply(
            lambda s: any(w in s for w in wanted)
        )
        df = df[mask].copy()

    if "country" in df.columns and "year" in df.columns:
        group_cols = ["country", "year"]
        keep_cols = [c for c in group_cols if c in df.columns]
        if keep_cols and "value" in df.columns:
            df = df.groupby(keep_cols, as_index=False)["value"].sum()

    return df.reset_index(drop=True)


def _fetch_pxweb(spec: dict) -> tuple[pd.DataFrame, str]:
    last_err: Exception | None = None
    for table in spec["table_candidates"]:
        try:
            payload = _query_capacity(table, spec.get("tech_filter"))
            df = _jsonstat_to_long(payload)
            if df.empty:
                last_err = IrenaError(f"empty payload for {table}")
                continue
            df = _normalise_capacity(df, spec.get("tech_filter"))
            if df.empty:
                last_err = IrenaError(f"no rows after tech_filter for {table}")
                continue
            return df, f"{PXWEB_BASE}/{table}"
        except (requests.RequestException, ValueError, IrenaError) as e:
            last_err = e
            continue
    raise IrenaError(f"PxWeb fetch failed for all candidate tables: {last_err}")


# ----------------------------------------------------------------------
# Manual-drop path
# ----------------------------------------------------------------------

def _fetch_manual(series_id: str, hint: str | None) -> tuple[pd.DataFrame, str]:
    """Locate a manual-drop file under data/manual/irena/ matching the hint.

    If multiple files exist (e.g. solar + wind LCOE), the hint substring is
    matched case-insensitively against the file name; otherwise the latest
    file is used.
    """
    try:
        path = find_latest("irena", "xlsx", "xls", "csv")
    except ManualDropError as e:
        raise IrenaError(
            f"{e}\n"
            f"Drop the latest IRENA Renewable Power Generation Costs "
            f"or Renewable Capacity Statistics file into data/manual/irena/."
        ) from e

    # Best-effort hint match within the manual-drop dir.
    if hint:
        try:
            from pathlib import Path
            candidates = [p for p in path.parent.iterdir()
                          if p.is_file() and hint.lower() in p.name.lower()
                          and p.suffix.lower() in (".xlsx", ".xls", ".csv")]
            if candidates:
                path = max(candidates, key=lambda p: (p.name, p.stat().st_mtime))
        except Exception:  # noqa: BLE001
            pass

    if series_id in {"lcoe_solar_pv", "lcoe_wind_onshore"} and path.suffix.lower() in (".xlsx", ".xls"):
        tech = {
            "lcoe_solar_pv": "Solar photovoltaic",
            "lcoe_wind_onshore": "Onshore wind",
        }[series_id]
        raw = pd.read_excel(path, sheet_name="Fig S.1", header=None)
        year_row = raw.apply(
            lambda row: pd.to_numeric(row, errors="coerce").between(1900, 2100).sum(),
            axis=1,
        ).idxmax()
        years = pd.to_numeric(raw.loc[year_row], errors="coerce")
        tech_rows = raw.index[raw.apply(lambda row: row.astype(str).str.contains(tech, case=False, regex=False).any(), axis=1)]
        if len(tech_rows) == 0:
            raise IrenaError(f"manual IRENA workbook did not contain technology row {tech!r}")
        values = pd.to_numeric(raw.loc[int(tech_rows[0])], errors="coerce")
        rows = []
        for col, year in years.dropna().items():
            value = values.get(col)
            if pd.notna(value):
                rows.append(
                    {
                        "country": "World",
                        "technology": tech,
                        "year": int(year),
                        "value": float(value) * 1000.0,
                        "value_original": float(value),
                        "original_units": "2024 USD/kWh",
                    }
                )
        df = pd.DataFrame(rows)
        if df.empty:
            raise IrenaError(f"manual IRENA workbook yielded no LCOE rows for {tech!r}")
        return df, f"manual://{path.name}#Fig S.1"

    if path.suffix.lower() in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        df = xls.parse(xls.sheet_names[0])
    else:
        df = pd.read_csv(path, low_memory=False)

    df.columns = [str(c).strip() for c in df.columns]
    # Normalise common patterns
    rename = {}
    for c in df.columns:
        cl = c.lower()
        if cl in ("country", "country/area", "region"):
            rename[c] = "country"
        elif cl in ("year", "period", "time"):
            rename[c] = "year"
        elif cl in ("value", "lcoe", "lcoe (usd/mwh)", "lcoe_usd_mwh"):
            rename[c] = "value"
    df = df.rename(columns=rename)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df, f"manual://{path.name}"


# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------

def fetch(
    series_id: str = "installed_capacity_renewable",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    series_id = SERIES_ALIASES.get(series_id, series_id)
    if series_id not in SUPPORTED:
        raise IrenaError(
            f"unsupported IRENA series_id {series_id!r}; "
            f"known: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    fetch_ts = utc_now()

    source_kind = spec["source"]
    if source_kind == "pxweb":
        try:
            df, src_url = _fetch_pxweb(spec)
        except IrenaError:
            # Auto-fallback to manual-drop with a tech hint based on series_id.
            hint_map = {
                "installed_capacity_solar_pv": "solar",
                "installed_capacity_wind": "wind",
                "installed_capacity_renewable": "capacity",
            }
            df, src_url = _fetch_manual(series_id, hint_map.get(series_id))
    elif source_kind == "manual":
        df, src_url = _fetch_manual(series_id, spec.get("manual_hint"))
    else:
        raise IrenaError(f"unknown source kind {source_kind!r} for {series_id}")

    if df.empty:
        raise IrenaError(f"IRENA {series_id} returned no rows")

    out, sha = write_vintage(
        publisher="irena",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    start = end = None
    if "year" in df.columns and df["year"].notna().any():
        start = str(int(df["year"].min()))
        end = str(int(df["year"].max()))

    return FetchResult(
        publisher="irena",
        series_id=series_id,
        source_url=src_url,
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec.get("frequency", "annual"),
        units=spec.get("units", "per IRENA metadata"),
        currency="USD" if "lcoe" in series_id else None,
        start_date=start,
        end_date=end,
        sha256=sha,
        parquet_path=out,
        extra={
            "desc": spec.get("desc"),
            "source_kind": source_kind,
            "columns": list(df.columns),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )


if __name__ == "__main__":
    import argparse
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.fetchers import irena as _self

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--series", default="installed_capacity_renewable",
                   choices=sorted(SUPPORTED))
    args = p.parse_args()
    res = _self.fetch(args.series)
    print(f"OK rows={res.rows} {res.start_date}->{res.end_date}")
    print(f"   {res.parquet_path}")
