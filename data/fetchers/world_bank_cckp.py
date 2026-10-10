"""World Bank Climate Change Knowledge Portal, observed CRU country series.

The official download selector supplies the exact URL below. The current
observational release is CRU TS4.10, annual 1901–2025, country-level, with
temperature (tas, degrees C) and precipitation (pr, accumulated mm).

The raw JSON can be source-locked without reading its measurement values via
``inspect_keys``. Do not call ``fetch`` for a prospective test until its
question, selectors, and decision rules have been registered in Git.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from ._base import ROOT, FetchResult, VINTAGES, utc_now, utc_stamp, write_vintage

SERIES_ID = "cru_ts4_10_tas_pr_annual_global"
SOURCE_URL = (
    "https://cckpapi.worldbank.org/api/v1/"
    "cru-x0.5_timeseries_tas,pr_timeseries_annual_1901-2025_"
    "mean_historical_cru_ts4.10_mean/global_countries?_format=json"
)
METHODOLOGY_URL = "https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html"
LICENSE = "CC-BY-4.0; credit World Bank CCKP and upstream CRU/UEA and Met Office"
_PERIOD = re.compile(r"^\d{4}-07$")
_COUNTRY = re.compile(r"^[A-Z]{3}$")


class ClimateSourceError(RuntimeError):
    pass


def _decode(raw: bytes) -> dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict) or (payload.get("metadata") or {}).get("status") != "success":
        raise ClimateSourceError("CCKP response metadata did not report success")
    data = payload.get("data")
    if not isinstance(data, dict) or set(data) != {"tas", "pr"}:
        raise ClimateSourceError("CCKP response must contain exact tas and pr objects")
    return data


def inspect_keys(raw: bytes) -> dict[str, Any]:
    """Inspect source structure and country/year keys only; skip measurements."""
    data = _decode(raw)
    key_sets: dict[str, set[tuple[str, str]]] = {}
    for variable, countries in data.items():
        if not isinstance(countries, dict):
            raise ClimateSourceError(f"{variable} is not a country-keyed object")
        keys: set[tuple[str, str]] = set()
        for country, periods in countries.items():
            if not _COUNTRY.fullmatch(country) or not isinstance(periods, dict):
                raise ClimateSourceError("invalid country code or period object")
            for period in periods.keys():
                if not _PERIOD.fullmatch(period):
                    raise ClimateSourceError(f"unexpected period key {period!r}")
                keys.add((country, period))
        key_sets[variable] = keys
    if key_sets["tas"] != key_sets["pr"]:
        raise ClimateSourceError("temperature and precipitation keys differ")
    common = key_sets["tas"]
    digest = hashlib.sha256("".join(f"{c}|{p}\n" for c, p in sorted(common)).encode()).hexdigest()
    return {
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
        "variables": ["pr", "tas"],
        "country_codes": len({country for country, _ in common}),
        "country_year_keys_per_variable": len(common),
        "first_year": min(int(period[:4]) for _, period in common),
        "last_year": max(int(period[:4]) for _, period in common),
        "key_sha256": digest,
        "source_period_format": "YYYY-07; annual observations, not July-only measurements",
    }


def fetch(
    series_id: str = SERIES_ID,
    *,
    vintage_utc: datetime | None = None,
    source_path: str | Path | None = None,
    expected_raw_sha256: str | None = None,
) -> FetchResult:
    """Materialize a pinned or freshly downloaded CCKP source after registration."""
    if series_id != SERIES_ID:
        raise ClimateSourceError(f"unsupported CCKP series {series_id!r}")
    fetch_ts = utc_now()
    if source_path is None:
        response = requests.get(SOURCE_URL, timeout=180)
        response.raise_for_status()
        raw = response.content
    else:
        raw = Path(source_path).read_bytes()
    key_info = inspect_keys(raw)
    if expected_raw_sha256 is not None and key_info["raw_sha256"] != expected_raw_sha256:
        raise ClimateSourceError("raw source checksum mismatch")

    raw_dir = VINTAGES / "world_bank_cckp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{SERIES_ID}@{utc_stamp(fetch_ts)}.json"
    raw_path.write_bytes(raw)

    data = _decode(raw)
    rows: list[dict[str, Any]] = []
    for variable in ("pr", "tas"):
        for country, periods in sorted(data[variable].items()):
            for period, value in sorted(periods.items()):
                rows.append({
                    "source_country_code": country,
                    # The pinned response contains KSV, which has no ISO 3166-1
                    # alpha-3 identity. Keep it in the source, but do not pass it
                    # to a country-level research join as if it were ISO3.
                    "country_iso3": None if country == "KSV" else country,
                    "year": int(period[:4]),
                    "source_period": period,
                    "variable_code": variable,
                    "value": value,
                    "unit": "mm" if variable == "pr" else "degC",
                })
    frame = pd.DataFrame(rows)
    parquet_path, parquet_sha = write_vintage(
        publisher="world_bank_cckp", series_id=series_id,
        frame=frame, fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher="world_bank_cckp",
        series_id=series_id,
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency="annual",
        units="tas: degC; pr: accumulated mm",
        currency=None,
        start_date=str(key_info["first_year"]),
        end_date=str(key_info["last_year"]),
        sha256=parquet_sha,
        parquet_path=parquet_path,
        extra={
            "raw_path": str(raw_path.relative_to(ROOT)),
            "raw_sha256": key_info["raw_sha256"],
            "key_sha256": key_info["key_sha256"],
            "source_release": "CRU TS4.10",
            "source_resolution": "0.5-degree gridded climate aggregated to countries by CCKP",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
