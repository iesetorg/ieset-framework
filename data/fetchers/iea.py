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

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage
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
    path = _find_manual_for_series(series_id)
    df = _read_any(path)
    if df.empty:
        raise IEAError(f"IEA manual file {path.name} parsed to 0 rows")

    out, sha = write_vintage(
        publisher="iea",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    return FetchResult(
        publisher="iea",
        series_id=series_id,
        source_url=f"manual://{path.name}",
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
            "manual_file": path.name,
            "n_columns": len(df.columns),
            "title": meta.get("title", ""),
            "publisher_source_url": meta.get(
                "source_url",
                "https://www.iea.org/data-and-statistics",
            ),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
