"""IMF World Economic Outlook fetcher via the IMF DataMapper API.

Endpoint: https://www.imf.org/external/datamapper/api/v1
Auth: none.
License: IMF standard permissions (attribution; citation required).

The DataMapper API returns JSON with shape:
    {"values": {"<series>": {"<country>": {"<year>": <number>, ...}}}}

Key indicators:
    NGDP_RPCH   Real GDP growth (annual %)
    NGDPDPC     GDP per capita (current USD)
    GGXWDG_NGDP General government gross debt (% GDP)
    GGR_NGDP    General government revenue (% GDP)
    GGX_NGDP    General government expenditure (% GDP)
    PCPIPCH     Inflation, end-of-period CPI (%)
    BCA_NGDPD   Current account balance (% GDP)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

IMF_BASE = "https://www.imf.org/external/datamapper/api/v1"
LICENSE = "IMF standard permissions (attribution required)"

# Cache of DataMapper-supported indicators. The DataMapper endpoint covers a
# curated subset of WEO + a few sister databases (~132 indicators). It does
# NOT cover IFS (International Financial Statistics) or BOP (Balance of
# Payments / IIP) series — those have to come through the SDMX endpoint or
# a dedicated fetcher (TBD). We cache the catalogue once per process to give
# clear "out-of-scope" errors instead of confusing "no values" messages.
_INDICATOR_CATALOGUE: set[str] | None = None


def _load_catalogue() -> set[str]:
    global _INDICATOR_CATALOGUE
    if _INDICATOR_CATALOGUE is not None:
        return _INDICATOR_CATALOGUE
    try:
        payload = _get("indicators")
        _INDICATOR_CATALOGUE = set((payload.get("indicators") or {}).keys())
    except Exception:
        # If the catalogue endpoint itself is down, fall back to "trust the
        # caller and try the fetch" — the per-series call will fail cleanly.
        _INDICATOR_CATALOGUE = set()
    return _INDICATOR_CATALOGUE


class ImfWeoError(RuntimeError):
    pass


class ImfNotInDataMapperError(ImfWeoError):
    """The series exists in IMF databases but the DataMapper API doesn't expose it.

    Common cause: IFS (International Financial Statistics) and BOP (Balance of
    Payments) indicators (BFOAFA, BFXFA, AREAER, FSI, etc.) live in databases
    not exposed through the DataMapper. They require the SDMX endpoint, which
    has a different schema and isn't yet wrapped by a fetcher in this repo.
    """


def _get(path: str) -> Any:
    r = requests.get(f"{IMF_BASE}/{path}", timeout=60)
    r.raise_for_status()
    return r.json()


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: list[str] | None = None,
) -> FetchResult:
    """Fetch a WEO indicator.

    countries: optional ISO3 list to filter client-side. The IMF datamapper API
               ignores URL-path country filters and always returns the full
               universe (plus aggregates like ADVEC, EMDE). We fetch everything
               and filter after parsing.

    Raises ImfNotInDataMapperError if the indicator is not in the DataMapper
    catalogue — typical for IFS/BOP series. Callers should treat that as
    "data not currently fetchable" rather than a fetch error.
    """
    fetch_ts = utc_now()
    catalogue = _load_catalogue()
    if catalogue and series_id not in catalogue:
        raise ImfNotInDataMapperError(
            f"{series_id} not in IMF DataMapper catalogue ({len(catalogue)} "
            f"indicators). Likely an IFS / BOP / AREAER series — needs a "
            f"separate SDMX-based fetcher (not yet implemented). Cite via a "
            f"different publisher (e.g. world_bank_wdi for current-account "
            f"flow proxies) until then."
        )
    payload = _get(series_id)
    values = (payload.get("values") or {}).get(series_id)
    if not values:
        raise ImfWeoError(f"IMF WEO returned no values for {series_id}")

    records: list[dict] = []
    for country_code, year_map in values.items():
        if not isinstance(year_map, dict):
            continue
        for year, val in year_map.items():
            records.append({
                "country_iso3": country_code,
                "year": int(year),
                "value": pd.to_numeric(val, errors="coerce"),
            })
    df = pd.DataFrame(records).sort_values(["country_iso3", "year"]).reset_index(drop=True)
    if countries:
        df = df[df["country_iso3"].isin(countries)].reset_index(drop=True)

    path_out, sha = write_vintage(
        publisher="imf",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    # Indicator metadata
    try:
        indicator_meta = _get(f"indicators/{series_id}")
        desc = (indicator_meta.get("indicators") or {}).get(series_id) or {}
    except requests.HTTPError:
        desc = {}

    return FetchResult(
        publisher="imf",
        series_id=series_id,
        source_url=f"{IMF_BASE}/{series_id}",
        methodology_url=f"https://www.imf.org/external/datamapper/{series_id}",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=desc.get("unit") or "per indicator definition",
        currency=None,
        start_date=str(df["year"].min()) if len(df) else None,
        end_date=str(df["year"].max()) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "indicator_label": desc.get("label"),
            "dataset": desc.get("dataset"),
            "countries_filter": countries or "all",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
