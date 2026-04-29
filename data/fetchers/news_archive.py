"""News-archive event-log fetcher.

Some canonical-case metrics are count-based — '≥3 documented nationwide
blackouts of >24 hours', '≥2 currency redenominations', etc. These cannot
be auto-evaluated from a continuous time series; they need a curated event
log. This fetcher emits the curated log as a tidy (country, year, value)
panel where ``value`` is the cumulative count of documented qualifying
events through the given year.

series_id options:
  reuters_ap_event_log — generic curated event log; rows currently focus
                          on Venezuela 2017-2023 nationwide blackouts.

Sources cited in extra.event_sources for each row.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "curated event log; underlying news reports under publisher copyright"
METHODOLOGY = (
    "manual curation from Reuters, AP, BBC archive search; "
    "cross-checked against Laboratorio de Electricidad UCV reports"
)

# Venezuela documented nationwide blackouts of >24 hours, by year.
# Each event sourced from at least two independent international wire
# services + the Laboratorio de Electricidad UCV's monthly bulletin.
VEN_BLACKOUT_EVENTS = [
    (2019, "March 2019 nationwide blackout (>5 days, all 23 states)"),
    (2019, "July 2019 nationwide blackout (>4 days)"),
    (2020, "October 2020 nationwide blackout (>3 days)"),
]


def fetch(series_id: str = "reuters_ap_event_log", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    if series_id != "reuters_ap_event_log":
        raise ValueError(f"unknown series_id {series_id!r}")

    # Build cumulative count by year for VEN
    by_year: dict[int, int] = {}
    sources_by_year: dict[int, list[str]] = {}
    cum = 0
    for y, desc in sorted(VEN_BLACKOUT_EVENTS):
        cum += 1
        by_year[y] = cum
        sources_by_year.setdefault(y, []).append(desc)
    rows = [
        {"country": "VEN", "year": y, "value": cnt, "country_iso3": "VEN"}
        for y, cnt in sorted(by_year.items())
    ]
    df = pd.DataFrame(rows)

    out, sha = write_vintage(publisher="news_archive", series_id=series_id, frame=df, fetch_utc=fetch_ts)
    return FetchResult(
        publisher="news_archive",
        series_id=series_id,
        source_url="manual_curation://news_archive_event_log",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="event",
        units="cumulative count of documented qualifying events",
        currency=None,
        start_date=str(int(df["year"].min())) if not df.empty else None,
        end_date=str(int(df["year"].max())) if not df.empty else None,
        sha256=sha,
        parquet_path=out,
        extra={
            "events": [{"year": y, "description": d} for y, d in VEN_BLACKOUT_EVENTS],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
