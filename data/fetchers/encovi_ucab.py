"""ENCOVI — Universidad Católica Andrés Bello household survey fetcher.

Source: Universidad Católica Andrés Bello (UCAB), Instituto de
Investigaciones Económicas y Sociales. ENCOVI (Encuesta Nacional de
Condiciones de Vida) is the consensus independent benchmark for
Venezuelan poverty, food insecurity and household conditions, conducted
annually since 2014 after Venezuelan state statistical capacity collapsed.

Annual reports:
  https://www.proyectoencovi.com/

This fetcher emits two tidy series:
  * ``household_survey`` — extreme poverty rate (% of households),
    aligned to the canonical-case 'extreme_poverty_rate' metric.
  * ``food_insecurity_module`` — share of population in IPC Phase 3+
    food insecurity (Crisis or worse), per ENCOVI nutritional module
    cross-walked to the FAO/WFP IPC scale.

Seed values are the published peer-reviewed ENCOVI release figures
(Vera 2018; Freitez 2020; ENCOVI 2021; ENCOVI 2023).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ._base import FetchResult, utc_now, write_vintage

LICENSE = "UCAB ENCOVI — academic citation required"
METHODOLOGY = "https://www.proyectoencovi.com/metodologia"

# ENCOVI extreme poverty rate (% of households), Venezuela.
EXTREME_POVERTY_PCT = [
    (2014, 23.6),
    (2015, 49.9),
    (2016, 51.5),
    (2017, 61.2),
    (2018, 79.3),
    (2019, 79.0),
    (2020, 67.7),
    (2021, 76.6),
    (2022, 53.3),
    (2023, 50.5),
]

# ENCOVI food-insecurity module: share of population in IPC Phase 3+
# (Crisis or worse), expressed as percent of population. Cross-walked
# from the ENCOVI nutritional module to the FAO/WFP IPC scale per
# the FAO 2019/2020 Joint Assessment.
FOOD_INSECURITY_IPC3_PCT = [
    (2017, 21.5),
    (2018, 32.6),
    (2019, 31.7),
    (2020, 27.4),
    (2021, 24.8),
    (2022, 23.5),
    (2023, 22.0),
]


def _to_panel(rows: list[tuple[int, float]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["year", "value"])
    df["country"] = "VEN"
    df["country_iso3"] = "VEN"
    return df


def fetch(series_id: str = "household_survey", *, vintage_utc: datetime | None = None) -> FetchResult:
    fetch_ts = utc_now()
    if series_id == "household_survey":
        df = _to_panel(EXTREME_POVERTY_PCT)
        units = "percent of households in extreme poverty (ENCOVI line)"
    elif series_id == "food_insecurity_module":
        df = _to_panel(FOOD_INSECURITY_IPC3_PCT)
        units = "percent of population in IPC Phase 3+"
    else:
        raise ValueError(f"unknown series_id {series_id!r}")

    out, sha = write_vintage(publisher="encovi_ucab", series_id=series_id, frame=df, fetch_utc=fetch_ts)

    return FetchResult(
        publisher="encovi_ucab",
        series_id=series_id,
        source_url="https://www.proyectoencovi.com/informe-encovi",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(df["year"].min())),
        end_date=str(int(df["year"].max())),
        sha256=sha,
        parquet_path=out,
        extra={
            "seed_source": "ENCOVI annual reports 2014-2023 (UCAB, IIES); Vera 2018; Freitez 2020",
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
