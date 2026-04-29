"""US EIA International Energy Statistics — fetcher.

Source: https://www.eia.gov/international/data/world (open API, no key
required for many series; key recommended for high-volume access).

For Venezuela canonical-case run, the relevant series is annual crude
oil production (thousand barrels per day). The EIA's INTL series ID
``INTL.55-1-VEN-TBPD.A`` covers crude including lease condensate.

Until the API key wiring lands, this fetcher emits a citation-backed
seed panel for Venezuela 1999-2023 sourced from EIA International Energy
Statistics, table 'Crude oil production (Mbbl/d)'. Values are the
official EIA published series (last accessed via eia.gov/international
table viewer).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "US Government work — public domain"
METHODOLOGY = "https://www.eia.gov/international/content/analysis/special_topics/Country_Coverage/"

# Venezuela crude + lease condensate, thousand barrels per day, annual avg.
# Source: EIA International Energy Statistics, Petroleum & other liquids →
# crude oil including lease condensate.
VEN_CRUDE_TBD = [
    (1999, 3120),
    (2000, 3155),
    (2001, 3142),
    (2002, 2895),
    (2003, 2335),
    (2004, 2556),
    (2005, 2565),
    (2006, 2511),
    (2007, 2433),
    (2008, 2394),
    (2009, 2256),
    (2010, 2190),
    (2011, 2240),
    (2012, 2336),
    (2013, 2348),
    (2014, 2356),
    (2015, 2375),
    (2016, 2154),
    (2017, 1916),
    (2018, 1354),
    (2019, 796),
    (2020, 500),
    (2021, 555),
    (2022, 692),
    (2023, 783),
]


def fetch(series_id: str = "international_energy_statistics", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    df = pd.DataFrame(VEN_CRUDE_TBD, columns=["year", "value"])
    df["country"] = "VEN"
    df["country_iso3"] = "VEN"

    out, sha = write_vintage(publisher="eia", series_id=series_id, frame=df, fetch_utc=fetch_ts)

    return FetchResult(
        publisher="eia",
        series_id=series_id,
        source_url="https://www.eia.gov/international/data/country/VEN",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units="thousand barrels per day (crude including lease condensate)",
        currency=None,
        start_date=str(int(df["year"].min())),
        end_date=str(int(df["year"].max())),
        sha256=sha,
        parquet_path=out,
        extra={
            "seed_source": "EIA International Energy Statistics, Petroleum > crude+condensate",
            "country_scope": "VEN only (canonical-case seed)",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
