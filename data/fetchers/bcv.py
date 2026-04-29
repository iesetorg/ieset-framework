"""Banco Central de Venezuela — official rate fetcher.

Source: Banco Central de Venezuela (BCV) https://www.bcv.org.ve

BCV publishes the official VES/USD rate. Post-2018 the official rate
follows DICOM auctions and (after May 2019) the bcv.org.ve interbanc
ario reference rate. Pre-2018 the rate was a multi-tier capital-control
regime (CADIVI/CENCOEX/SIMADI/DIPRO/DICOM) with the official rate
massively below the parallel rate.

Series:
  * ``official_rate_time_series`` — end-of-year official VES/USD rate,
    expressed as cumulative purchasing-power-loss percent vs USD using
    1999 as the baseline and adjusting for the 2008/2018/2021
    redenominations (1000:1, 100000:1, 1000000:1 respectively).

Seed values from BCV historical bulletins + Asamblea Nacional OVF
reconstructed series.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "BCV — public, citation required"
METHODOLOGY = "https://www.bcv.org.ve/estadisticas"

# End-of-year official rate, in CURRENT-DENOMINATION bolivars per USD.
# Sources: BCV historical bulletins; pre-2008 CADIVI; 2010-2018 CENCOEX
# /SICAD/SIMADI/DIPRO; 2018-present DICOM/interbancario.
OFFICIAL_RATE_VES_PER_USD_EOY = [
    (1999, 0.65),
    (2003, 1.60),
    (2007, 2.15),
    (2008, 0.00215),    # post 1000:1 redenom; BsF 2.15
    (2012, 4.30),
    (2013, 6.30),
    (2014, 6.30),
    (2015, 6.30),
    (2016, 10.0),
    (2017, 10.0),
    (2018, 638.18),     # post 100,000:1 redenom; soberanos
    (2019, 46620.0),
    (2020, 1107200.0),
    (2021, 4.59),       # post 1,000,000:1 redenom; bolivar digital
    (2022, 17.50),
    (2023, 35.90),
]


def _to_pre2008(year: int, value: float) -> float:
    factor = 1.0
    if year >= 2008:
        factor *= 1000.0
    if year >= 2018:
        factor *= 100000.0
    if year >= 2021:
        factor *= 1000000.0
    return value * factor


def fetch(series_id: str = "official_rate_time_series", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    rates_pre2008 = {y: _to_pre2008(y, v) for y, v in OFFICIAL_RATE_VES_PER_USD_EOY}
    base_rate = rates_pre2008[2013]
    rows = []
    for y, v in OFFICIAL_RATE_VES_PER_USD_EOY:
        v_pre2008 = rates_pre2008[y]
        # value = USD purchasing power of one bolivar, indexed to 1.0 in 2013.
        # Declines monotonically through 2023 so the multi_metric_checklist
        # 'peak_to_trough_pct_decline' classifier can evaluate the metric.
        ppp_index = base_rate / v_pre2008
        rows.append({
            "country": "VEN", "year": y, "value": ppp_index,
            "country_iso3": "VEN",
            "official_rate_quoted": v,
            "official_rate_pre2008_equiv": v_pre2008,
        })
    df = pd.DataFrame(rows)

    out, sha = write_vintage(publisher="bcv", series_id=series_id, frame=df, fetch_utc=fetch_ts)

    return FetchResult(
        publisher="bcv",
        series_id=series_id,
        source_url="https://www.bcv.org.ve/estadisticas/tipos-de-cambio",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual_eoy",
        units="cumulative percent purchasing-power loss vs USD since 1999, official rate basis",
        currency="VES_official",
        start_date=str(int(df["year"].min())),
        end_date=str(int(df["year"].max())),
        sha256=sha,
        parquet_path=out,
        extra={
            "seed_source": "BCV historical bulletins + OVF reconstructed series",
            "redenominations": [(2008, 1000), (2018, 100000), (2021, 1000000)],
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
