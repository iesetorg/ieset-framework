"""IMF Primary Commodity Price System (PCPS) fetcher via the IMF DataMapper API.

Endpoint: https://www.imf.org/external/datamapper/api/v1
Auth: none.
License: IMF standard permissions (attribution; citation required).

PCPS ships commodity prices (oil, gas, metals, agricultural) through the same
DataMapper API shape as WEO:
    {"values": {"<series>": {"<region>": {"<period>": <number>, ...}}}}

For PCPS the outer region key is typically "W00" (world) since commodity prices
are global. Periods may be annual ("2020") or monthly ("2020M01") depending on
the series. This fetcher tolerates both the nested shape (region -> period ->
value) observed in WEO and a flat shape (period -> value) in case the PCPS
endpoint omits the region layer.

Key indicators (verified against the IMF PCPS series catalogue):
    POILAPSP   Average petroleum spot price (Brent/WTI/Dubai avg, USD/bbl)
    POILBRE    Brent crude oil (USD/bbl)
    POILWTI    WTI crude oil (USD/bbl)
    PNGASEU    Natural gas, Europe (USD/mmbtu)
    PNGASUS    Natural gas, US (USD/mmbtu)
    PGOLD      Gold (USD/troy oz)
    PCOPP      Copper (USD/mt)
    PALUM      Aluminum (USD/mt)
    PWHEAMT    Wheat (USD/mt)
    PCORN      Corn (USD/mt)
    PSOYB      Soybeans (USD/mt)
    PCOFFOTM   Coffee, Other Mild Arabicas (USD/lb)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

IMF_BASE = "https://www.imf.org/external/datamapper/api/v1"
METHODOLOGY = "https://www.imf.org/en/Research/commodity-prices"
LICENSE = "IMF standard permissions (attribution required)"


class ImfPcpsError(RuntimeError):
    pass


def _get(path: str) -> Any:
    r = requests.get(f"{IMF_BASE}/{path}", timeout=60)
    r.raise_for_status()
    return r.json()


def _infer_frequency(periods: pd.Series) -> str:
    s = periods.astype(str)
    if s.str.contains("M", na=False).any():
        return "monthly"
    if s.str.contains("Q", na=False).any():
        return "quarterly"
    return "annual"


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
) -> FetchResult:
    """Fetch a PCPS commodity series.

    PCPS prices are global (not country-specific); the DataMapper response may
    key values under a region code (e.g. "W00") or drop the region layer
    entirely. We flatten either shape to a ``(region, period, value)`` frame.
    """
    fetch_ts = utc_now()
    payload = _get(series_id)
    values = (payload.get("values") or {}).get(series_id)
    if not values:
        raise ImfPcpsError(f"IMF PCPS returned no values for {series_id}")

    records: list[dict] = []
    for outer_key, inner in values.items():
        if isinstance(inner, dict):
            # nested: region -> period -> value (WEO-style shape)
            for period, val in inner.items():
                records.append({
                    "region": outer_key,
                    "period": str(period),
                    "value": pd.to_numeric(val, errors="coerce"),
                })
        else:
            # flat: period -> value (no region layer)
            records.append({
                "region": "W00",
                "period": str(outer_key),
                "value": pd.to_numeric(inner, errors="coerce"),
            })

    df = pd.DataFrame(records).sort_values(["region", "period"]).reset_index(drop=True)

    path_out, sha = write_vintage(
        publisher="imf_pcps",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    # Indicator metadata — same endpoint as WEO indicators namespace
    desc: dict[str, Any] = {}
    try:
        indicator_meta = _get(f"indicators/{series_id}")
        desc = (indicator_meta.get("indicators") or {}).get(series_id) or {}
    except requests.HTTPError:
        pass

    frequency = _infer_frequency(df["period"]) if len(df) else "annual"

    return FetchResult(
        publisher="imf_pcps",
        series_id=series_id,
        source_url=f"{IMF_BASE}/{series_id}",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=frequency,
        units=desc.get("unit") or "per indicator definition",
        currency="USD",
        start_date=str(df["period"].min()) if len(df) else None,
        end_date=str(df["period"].max()) if len(df) else None,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "indicator_label": desc.get("label"),
            "dataset": desc.get("dataset") or "PCPS",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
