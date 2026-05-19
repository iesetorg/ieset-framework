"""International Energy Agency (IEA) — manual-drop + opportunistic-URL fetcher.

Source URL (browser):
    https://www.iea.org/data-and-statistics/data-product

Reality check: most IEA core data (World Energy Statistics, Balances, the
WEO datasets) is paywalled and behind academic subscriptions. The handful
of free public datasets are:

  - Energy Prices (industrial electricity / industrial natural gas) —
    quarterly tracker, distributed as free CSV/XLSX downloads but the
    download URL is generated per-publication and rotates each release.
  - Fossil-Fuel Subsidies tracker — annual estimates of consumption
    subsidies; free CSV from the IEA data hub.
  - CO2 Emissions from Fuel Combustion (Highlights) — free aggregated
    country-year totals, distributed as a CSV.

In practice every "free" IEA CSV sits behind a Cloudflare gate that
blocks plain `requests.get` (returns 403 / a JS challenge page). Until a
headless-browser scraper lands, the supported pattern is **manual drop**:
users download the CSV / XLSX from the IEA site and place it under
``data/manual/iea/<series_id>/`` (one subdir per series so files don't
collide). The fetcher picks the latest matching file for the requested
series.

Canonical series for IESET:
    industrial_electricity_price       — IEA Energy Prices, industrial
                                         electricity price ($/MWh).
    fossil_subsidies_estimate          — IEA Fossil Fuel Subsidies tracker,
                                         consumption subsidies (USDbn).
    co2_emissions_from_fuel_combustion — IEA CO2 Highlights, country-year
                                         CO2 emissions from fuel combustion
                                         (Mt CO2).
"""
from __future__ import annotations

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
from ._http import get as robust_get
from ._manual_utils import MANUAL_ROOT, ManualDropError

LICENSE = "academic_citation"  # IEA terms — non-commercial, attribution.

# Per-series metadata. URL fields are documentation only; the fetcher reads
# from data/manual/iea/<series_id>/ because every IEA download URL is
# Cloudflare-gated.
SUPPORTED: dict[str, dict[str, Any]] = {
    "industrial_electricity_price": {
        "title": "IEA Energy Prices — industrial electricity price (quarterly)",
        "frequency": "quarterly",
        "currency": "USD",
        "units": "USD per MWh (industrial end-user, tax-inclusive where published)",
        "source_url": (
            "https://www.iea.org/data-and-statistics/data-product/energy-prices"
        ),
        "methodology_url": (
            "https://www.iea.org/reports/energy-prices-2024"
        ),
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/energy-prices",
    },
    "fossil_subsidies_estimate": {
        "title": "IEA Fossil-Fuel Subsidies tracker — consumption subsidies (annual)",
        "frequency": "annual",
        "currency": "USD",
        "units": "USD billion (consumption subsidies, by country and product)",
        "source_url": (
            "https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database"
        ),
        "methodology_url": (
            "https://www.iea.org/topics/fossil-fuel-subsidies"
        ),
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database",
    },
    "co2_emissions_from_fuel_combustion": {
        "title": "IEA CO2 Emissions from Fuel Combustion — Highlights (annual)",
        "frequency": "annual",
        "currency": None,
        "units": "Mt CO2 (country-year, fuel-combustion only)",
        "source_url": (
            "https://www.iea.org/data-and-statistics/data-product/"
            "greenhouse-gas-emissions-from-energy-highlights"
        ),
        "methodology_url": (
            "https://www.iea.org/reports/co2-emissions-in-2023"
        ),
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/greenhouse-gas-emissions-from-energy-highlights",
    },
    "electricity_statistics": {
        "title": "IEA electricity statistics / monthly electricity data",
        "frequency": "monthly",
        "currency": None,
        "units": "per IEA electricity data metadata",
        "source_url": "https://www.iea.org/data-and-statistics/data-product/monthly-electricity-statistics",
        "methodology_url": "https://www.iea.org/data-and-statistics/data-product/monthly-electricity-statistics",
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/monthly-electricity-statistics",
    },
    "electricity_balance": {
        "title": "IEA electricity statistics / electricity balance",
        "frequency": "annual",
        "currency": None,
        "units": "per IEA electricity data metadata",
        "source_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
        "methodology_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
    },
    "nuclear_capacity_factor": {
        "title": "IEA electricity statistics / nuclear generation and capacity proxy",
        "frequency": "annual",
        "currency": None,
        "units": "per IEA electricity data metadata",
        "source_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
        "methodology_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/electricity-information",
    },
    "electricity_consumption_per_capita": {
        "title": "IEA electricity consumption per-capita inputs",
        "frequency": "annual",
        "currency": None,
        "units": "per IEA electricity data metadata",
        "source_url": "https://www.iea.org/data-and-statistics/data-product/world-energy-balances",
        "methodology_url": "https://www.iea.org/data-and-statistics/data-product/world-energy-balances",
        "landing_url": "https://www.iea.org/data-and-statistics/data-product/world-energy-balances",
    },
}


class IEAError(RuntimeError):
    pass


def _find_manual_for_series(series_id: str) -> Path:
    """Locate the latest manual-drop file for a given IEA series.

    Convention: data/manual/iea/<series_id>/<file>.{csv,xlsx,xls,zip}.
    Falls back to data/manual/iea/ root if the per-series subdir is empty
    (lets a single drop satisfy a single series quickly during bootstrap).
    """
    accepted = (".csv", ".xlsx", ".xls")
    series_dir = MANUAL_ROOT / "iea" / series_id
    candidates: list[Path] = []
    if series_dir.exists():
        candidates = [
            p for p in series_dir.iterdir()
            if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in accepted
        ]
    if not candidates:
        root_dir = MANUAL_ROOT / "iea"
        if root_dir.exists():
            candidates = [
                p for p in root_dir.iterdir()
                if p.is_file()
                and not p.name.startswith(".")
                and p.suffix.lower() in accepted
                and series_id in p.stem.lower()
            ]
    if not candidates:
        raise ManualDropError(
            f"No IEA manual-drop file for series '{series_id}'. "
            f"Drop a .csv/.xlsx into data/manual/iea/{series_id}/ "
            f"(or name a file in data/manual/iea/ to include '{series_id}' in its stem)."
        )
    return max(candidates, key=lambda p: (p.name, p.stat().st_mtime))


def _candidate_downloads(html: str) -> list[str]:
    urls = re.findall(r"https?://[^\"'<> )]+", html)
    hrefs = re.findall(r"""href=["']([^"']+)["']""", html, flags=re.I)
    urls.extend(h for h in hrefs if h.startswith("https://"))
    wanted = []
    for url in urls:
        clean = url.replace("\\u0026", "&").replace("&amp;", "&")
        if re.search(r"\.(csv|xlsx?|zip)(?:\?|$)", clean, flags=re.I):
            wanted.append(clean)
        elif "download" in clean.lower() and any(token in clean.lower() for token in ("csv", "xlsx", "xls", "zip")):
            wanted.append(clean)
    # Preserve order while de-duping.
    seen: set[str] = set()
    out: list[str] = []
    for url in wanted:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _read_any(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        xls = pd.ExcelFile(path)
        # IEA workbooks usually carry a coverage / notes sheet first; pick the
        # widest sheet by row count as a robust default.
        best_name = max(
            xls.sheet_names,
            key=lambda s: len(xls.parse(s, nrows=0).columns),
        )
        df = xls.parse(best_name)
    else:
        df = pd.read_csv(path)
    for c in df.columns:
        if df[c].dtype == "object":
            df[c] = df[c].astype("string")
    return df


def _read_payload(content: bytes, content_type: str | None) -> pd.DataFrame:
    if content[:2] == b"PK" and content[:4] == b"PK\x03\x04":
        try:
            return pd.read_excel(io.BytesIO(content))
        except Exception:
            pass
    if content[:2] == b"PK" or (content_type and "zip" in content_type.lower()):
        z = zipfile.ZipFile(io.BytesIO(content))
        names = [n for n in z.namelist() if n.lower().endswith((".csv", ".xlsx", ".xls"))]
        if not names:
            raise IEAError(f"download zip contains no csv/xlsx files: {z.namelist()[:8]}")
        with z.open(names[0]) as handle:
            payload = handle.read()
        return _read_payload(payload, "application/octet-stream")
    try:
        return pd.read_csv(io.BytesIO(content), low_memory=False)
    except Exception:
        return pd.read_excel(io.BytesIO(content))


def _fetch_official_download(series_id: str, meta: dict[str, Any]) -> tuple[pd.DataFrame, str, str]:
    landing = meta.get("landing_url") or meta.get("source_url")
    if not landing:
        raise IEAError(f"no landing URL registered for {series_id}")
    page = robust_get(
        landing,
        timeout=180,
        return_http_errors=True,
        zenrows_js_render=True,
    )
    if page.status_code >= 400:
        raise IEAError(f"IEA landing page HTTP {page.status_code} for {series_id} via {page.transport}")
    downloads = _candidate_downloads(page.text)
    if not downloads:
        raise IEAError(f"no public CSV/XLSX download link found on {landing}")
    last_err: Exception | None = None
    for url in downloads:
        try:
            payload = robust_get(
                url,
                timeout=240,
                headers={"Accept": "text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"},
            )
            df = _read_payload(payload.content, payload.content_type)
            if not df.empty:
                return df, url, payload.transport
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
    raise IEAError(f"all discovered IEA downloads failed for {series_id}: {last_err}")


def fetch(
    series_id: str = "industrial_electricity_price",
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch an IEA series from the manual-drop directory.

    series_id: a key in SUPPORTED; unknown ids are accepted and treated
               as a free-form alias matched against filenames in
               data/manual/iea/.
    """
    fetch_ts = utc_now()
    meta = SUPPORTED.get(series_id, {})
    source_url = ""
    transport = ""
    manual_file = None
    try:
        df, source_url, transport = _fetch_official_download(series_id, meta)
    except Exception:
        path = _find_manual_for_series(series_id)
        df = _read_any(path)
        source_url = f"manual://{path.name}"
        transport = "manual_drop"
        manual_file = path.name
    if df.empty:
        raise IEAError(f"IEA {series_id} parsed to 0 rows")

    out, sha = write_vintage(
        publisher="iea",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="iea",
        series_id=series_id,
        source_url=source_url,
        methodology_url=meta.get(
            "methodology_url",
            "https://www.iea.org/data-and-statistics",
        ),
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=meta.get("frequency", "annual"),
        units=meta.get("units", "per IEA publication metadata"),
        currency=meta.get("currency"),
        start_date=None,
        end_date=None,
        sha256=sha,
        parquet_path=out,
        extra={
            "manual_file": manual_file,
            "n_columns": len(df.columns),
            "title": meta.get("title", ""),
            "transport": transport,
            "publisher_source_url": meta.get(
                "source_url",
                "https://www.iea.org/data-and-statistics",
            ),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
