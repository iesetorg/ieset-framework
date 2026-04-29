"""World Bank Worldwide Governance Indicators (WGI) fetcher.

Uses the generic World Bank API with source=3 (WGI databank) instead of
source=2 (WDI). Same pagination + license as WDI (CC-BY-4.0), same response
shape.

Key indicators (Kaufmann-Kraay-Mastruzzi, annual since 1996) — note that the
World Bank migrated WGI codes in 2024 to the `GOV_WGI_` prefix:
    GOV_WGI_VA.EST  Voice and Accountability
    GOV_WGI_PV.EST  Political Stability and Absence of Violence/Terrorism
    GOV_WGI_GE.EST  Government Effectiveness
    GOV_WGI_RQ.EST  Regulatory Quality
    GOV_WGI_RL.EST  Rule of Law
    GOV_WGI_CC.EST  Control of Corruption
Each pillar also has .SC (0-100 score), .SE (standard error), .SR (source count),
and .SC_LB / .SC_UB (90% CI bounds) companions.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

WB_BASE = "https://api.worldbank.org/v2"
WGI_SOURCE_ID = 3  # WGI databank
LICENSE = "CC-BY-4.0"

# WGI migrated indicator codes in 2024 from `<pillar>.EST` (e.g. `CC.EST`)
# to the `GOV_WGI_<pillar>.EST` prefix. The old codes return an "Invalid
# value" payload. Map common short forms to the modern code so legacy
# citations (and the natural-language pillar names) resolve.
_WGI_CODE_MAP = {
    "VA.EST": "GOV_WGI_VA.EST",
    "PV.EST": "GOV_WGI_PV.EST",
    "GE.EST": "GOV_WGI_GE.EST",
    "RQ.EST": "GOV_WGI_RQ.EST",
    "RL.EST": "GOV_WGI_RL.EST",
    "CC.EST": "GOV_WGI_CC.EST",
    "VoiceAndAccountability": "GOV_WGI_VA.EST",
    "PoliticalStability": "GOV_WGI_PV.EST",
    "GovernmentEffectiveness": "GOV_WGI_GE.EST",
    "RegulatoryQuality": "GOV_WGI_RQ.EST",
    "RuleOfLaw": "GOV_WGI_RL.EST",
    "ControlOfCorruption": "GOV_WGI_CC.EST",
}


def _resolve_code(indicator: str) -> str:
    """Map deprecated short WGI codes to current `GOV_WGI_*` codes."""
    return _WGI_CODE_MAP.get(indicator, indicator)


class WgiError(RuntimeError):
    pass


def _iter_pages(indicator: str, countries: str) -> Iterable[dict]:
    page = 1
    while True:
        r = requests.get(
            f"{WB_BASE}/country/{countries}/indicator/{indicator}",
            params={"format": "json", "per_page": 1000, "page": page, "source": WGI_SOURCE_ID},
            timeout=60,
        )
        r.raise_for_status()
        payload = r.json()
        if not isinstance(payload, list):
            raise WgiError(f"unexpected payload shape for {indicator}: {type(payload)}")
        # Single-element responses are WB error messages — the indicator code is invalid.
        if len(payload) < 2:
            err = payload[0] if payload else {}
            msg = ""
            if isinstance(err, dict):
                msgs = err.get("message") or []
                if msgs and isinstance(msgs, list):
                    msg = "; ".join(f"{m.get('key')}: {m.get('value')}" for m in msgs)
            raise WgiError(f"WGI api returned error for {indicator}: {msg}")
        meta, rows = payload
        if rows is None:
            return
        for row in rows:
            yield row
        if page >= int(meta.get("pages", 1)):
            return
        page += 1


def fetch(
    series_id: str,
    *,
    vintage_utc: datetime | None = None,
    countries: str = "all",
) -> FetchResult:
    fetch_ts = utc_now()
    resolved = _resolve_code(series_id)
    rows = list(_iter_pages(resolved, countries))
    if not rows:
        raise WgiError(f"WGI returned no rows for {series_id} (resolved={resolved})")

    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"] = pd.to_numeric(df["date"], errors="coerce").astype("Int64")
    df["country_iso3"] = df["countryiso3code"]
    df["country_name"] = df["country"].apply(lambda c: c.get("value") if isinstance(c, dict) else None)
    df["indicator_id"] = df["indicator"].apply(lambda i: i.get("id") if isinstance(i, dict) else None)
    df = (
        df[["country_iso3", "country_name", "indicator_id", "year", "value"]]
        .dropna(subset=["country_iso3"])
        .sort_values(["country_iso3", "year"])
        .reset_index(drop=True)
    )

    path, sha = write_vintage(
        publisher="wgi",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    meta_resp = requests.get(
        f"{WB_BASE}/indicator/{series_id}",
        params={"format": "json", "source": WGI_SOURCE_ID},
        timeout=30,
    )
    meta_resp.raise_for_status()
    meta_payload = meta_resp.json()
    meta = (
        meta_payload[1][0]
        if isinstance(meta_payload, list) and len(meta_payload) > 1 and meta_payload[1]
        else {}
    )

    return FetchResult(
        publisher="wgi",
        series_id=series_id,
        source_url=f"{WB_BASE}/country/{countries}/indicator/{series_id}?format=json&source={WGI_SOURCE_ID}",
        methodology_url="https://www.worldbank.org/en/publication/worldwide-governance-indicators",
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="WGI point estimate (approx. -2.5 to 2.5; std.err. available)",
        currency=None,
        start_date=str(df["year"].min()) if len(df) else None,
        end_date=str(df["year"].max()) if len(df) else None,
        sha256=sha,
        parquet_path=path,
        extra={
            "indicator_name": meta.get("name"),
            "source_note": (meta.get("sourceNote") or "")[:400],
            "countries_param": countries,
            "wb_source_id": WGI_SOURCE_ID,
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
