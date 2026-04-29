"""OECD Product Market Regulation (PMR) indicators.

Separate publisher namespace from general OECD data because PMR has its own
methodology, release cadence, and axis-level relevance (gates the regulatory
axes per handoff Update 2). Internally a thin wrapper that reuses the shared
SDMX client in data.fetchers.oecd.

Canonical dataflow IDs (verified 2026-04 via the OECD dataflow catalogue):
    OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.2       Economy-wide PMR indicators
    OECD.ECO.GCRD,DSD_PMR@DF_PMR_WBG,1.2   PMR aggregates incl. World Bank Group
"""
from __future__ import annotations

from datetime import datetime

from . import oecd as _oecd
from ._base import FetchResult


def fetch(series_id: str, *, vintage_utc: datetime | None = None, **kwargs) -> FetchResult:
    return _oecd.fetch(series_id, vintage_utc=vintage_utc, publisher_id="oecd_pmr", **kwargs)
