"""US Census Bureau — fetcher.

Endpoint family: https://api.census.gov/data/<year>/<dataset>
Auth: optional. Free key from https://api.census.gov/data/key_signup.html.
      Read from env var ``CENSUS_API_KEY`` if set; without a key the public
      endpoints work but are rate-limited.
License: US Government work — public domain.

This fetcher covers the nine series cited in the IESET long-tail spec:

    ACS                                — ACS 5-year umbrella pull (median HH income, total pop)
    acs_education_attainment           — ACS 5-year educational attainment (B15003)
    acs_school_enrollment              — ACS 5-year school enrollment (B14001)
    annual_state_population_estimates  — Population Estimates Program, state-level
    building_permits                   — Building Permits Survey (national, monthly EITS)
    cps_supplemental_poverty           — CPS ASEC supplemental poverty measure
    population                         — Population Estimates Program, national
    saipe                              — Small Area Income and Poverty Estimates (state)
    trade_in_goods                     — International Trade — exports of goods (HS, monthly)

Each series resolves to a (dataset_path, get_vars, geo_predicate, year, frequency)
tuple in ``SUPPORTED``. The fetcher GETs the resulting JSON, normalises it to a
tidy frame with ``country_iso3="USA"``, ``year``, ``value``, and a ``geo_area``
column, then persists via ``write_vintage``.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests

from ._base import FetchResult, utc_now, write_vintage

CENSUS_BASE = "https://api.census.gov/data"
LICENSE = "US Government work — public domain"
METHODOLOGY = "https://www.census.gov/data/developers/data-sets.html"


class CensusError(RuntimeError):
    pass


# Each entry: (dataset_path, list_of_get_vars, geo_predicate_dict, year_or_none, frequency, units, value_var)
# - dataset_path is appended to /data/<year>/<dataset_path> when year present, or
#   /data/<dataset_path> when None (timeseries).
# - geo_predicate: {"for": "...", "in": "..."} merged into params.
# - value_var picks the column in the response treated as the numeric "value".
SUPPORTED: dict[str, dict[str, Any]] = {
    # ACS umbrella — total population + median household income for all states.
    "ACS": {
        "year": 2022,
        "dataset": "acs/acs5",
        "get": ["NAME", "B01003_001E", "B19013_001E"],
        "geo": {"for": "state:*"},
        "frequency": "annual",
        "units": "persons; USD (median household income)",
        "value_var": "B19013_001E",
    },
    "acs_education_attainment": {
        "year": 2022,
        "dataset": "acs/acs5",
        # B15003_001E = total pop 25+; _022E = bachelor's; _023E = master's;
        # _024E = professional; _025E = doctorate.
        "get": [
            "NAME",
            "B15003_001E",
            "B15003_022E",
            "B15003_023E",
            "B15003_024E",
            "B15003_025E",
        ],
        "geo": {"for": "state:*"},
        "frequency": "annual",
        "units": "persons (educational attainment counts, age 25+)",
        "value_var": "B15003_022E",
    },
    "acs_school_enrollment": {
        "year": 2022,
        "dataset": "acs/acs5",
        # B14001_001E = total pop 3+; _002E = enrolled in school.
        "get": ["NAME", "B14001_001E", "B14001_002E"],
        "geo": {"for": "state:*"},
        "frequency": "annual",
        "units": "persons (enrolled in school)",
        "value_var": "B14001_002E",
    },
    "annual_state_population_estimates": {
        "year": 2022,
        "dataset": "pep/population",
        "get": ["NAME", "POP_2022"],
        "geo": {"for": "state:*"},
        "frequency": "annual",
        "units": "persons",
        "value_var": "POP_2022",
    },
    "population": {
        "year": 2022,
        "dataset": "pep/population",
        "get": ["NAME", "POP_2022"],
        "geo": {"for": "us:*"},
        "frequency": "annual",
        "units": "persons (US national)",
        "value_var": "POP_2022",
    },
    "saipe": {
        # Small Area Income and Poverty Estimates — timeseries.
        "year": None,
        "dataset": "timeseries/poverty/saipe",
        "get": ["NAME", "SAEPOVRTALL_PT", "SAEMHI_PT", "YEAR"],
        "geo": {"for": "state:*"},
        "extra_params": {"time": "from 2018 to 2022"},
        "frequency": "annual",
        "units": "percent (poverty rate); USD (median household income)",
        "value_var": "SAEPOVRTALL_PT",
    },
    "cps_supplemental_poverty": {
        # CPS ASEC March supplement — supplemental poverty measure flag (SPM_POVUNIT_POV).
        # National-level pull keeps payload small; weight is MARSUPWT.
        "year": 2022,
        "dataset": "cps/asec/mar",
        "get": ["SPM_POVUNIT_POV", "MARSUPWT", "AGE", "STATEFIP"],
        "geo": {"for": "us:*"},
        "frequency": "annual",
        "units": "household-level supplemental poverty flag (0/1) with weight",
        "value_var": "SPM_POVUNIT_POV",
    },
    "building_permits": {
        # Economic Indicators Time Series — Building Permits Survey, national.
        "year": None,
        "dataset": "timeseries/eits/bps",
        "get": ["cell_value", "data_type_code", "time_slot_id", "error_data", "category_code", "seasonally_adj"],
        "geo": None,
        "extra_params": {
            "time": "from 2020 to 2023",
            "category_code": "00",  # total
            "data_type_code": "TOTAL",  # total permits
            "seasonally_adj": "yes",
        },
        "frequency": "monthly",
        "units": "housing units authorized by building permits (national, SA)",
        "value_var": "cell_value",
    },
    "trade_in_goods": {
        # International Trade exports — HS-coded monthly.
        "year": None,
        "dataset": "timeseries/intltrade/exports/hs",
        "get": ["CTY_CODE", "CTY_NAME", "ALL_VAL_MO", "ALL_VAL_YR", "YEAR", "MONTH"],
        "geo": None,
        "extra_params": {"time": "from 2023-01 to 2023-12"},
        "frequency": "monthly",
        "units": "USD (export value, all-commodity totals by partner country)",
        "value_var": "ALL_VAL_MO",
    },
}


def _build_url(spec: dict[str, Any]) -> str:
    if spec["year"] is None:
        return f"{CENSUS_BASE}/{spec['dataset']}"
    return f"{CENSUS_BASE}/{spec['year']}/{spec['dataset']}"


def _build_params(spec: dict[str, Any], api_key: str | None) -> dict[str, str]:
    params: dict[str, str] = {"get": ",".join(spec["get"])}
    geo = spec.get("geo") or {}
    for k, v in geo.items():
        params[k] = v
    for k, v in spec.get("extra_params", {}).items():
        params[k] = v
    if api_key:
        params["key"] = api_key
    return params


def _request(url: str, params: dict[str, str]) -> list[list[Any]]:
    r = requests.get(url, params=params, timeout=120)
    if r.status_code != 200:
        raise CensusError(
            f"Census API error {r.status_code} for {url} params={params}: {r.text[:300]}"
        )
    try:
        payload = r.json()
    except ValueError as e:
        raise CensusError(f"Census non-JSON response from {url}: {r.text[:200]}") from e
    if not isinstance(payload, list) or len(payload) < 2:
        raise CensusError(f"Census empty/malformed payload from {url}: {payload}")
    return payload


def fetch(series_id: str, *, vintage_utc: datetime | None = None) -> FetchResult:
    """Fetch one cited Census series.

    series_id must be a key of ``SUPPORTED``.
    """
    if series_id not in SUPPORTED:
        raise CensusError(
            f"Unknown series_id '{series_id}'. Supported: {sorted(SUPPORTED)}"
        )
    spec = SUPPORTED[series_id]
    fetch_ts = utc_now()
    api_key = os.environ.get("CENSUS_API_KEY")

    url = _build_url(spec)
    params = _build_params(spec, api_key)
    payload = _request(url, params)

    header, *rows = payload
    df = pd.DataFrame(rows, columns=header)

    # Common normalisation: country, geo_area, year, value.
    df["country_iso3"] = "USA"
    if "NAME" in df.columns:
        df["geo_area"] = df["NAME"]
    elif "state" in df.columns:
        df["geo_area"] = df["state"]
    else:
        df["geo_area"] = "USA"

    # Year column: datasets vary.
    if spec["year"] is not None:
        df["year"] = int(spec["year"])
    elif "YEAR" in df.columns:
        df["year"] = pd.to_numeric(df["YEAR"], errors="coerce").astype("Int64")
    elif "time" in df.columns:
        # EITS returns "time" like "2023-04".
        df["year"] = pd.to_numeric(df["time"].astype(str).str[:4], errors="coerce").astype("Int64")
    else:
        df["year"] = pd.NA

    value_var = spec["value_var"]
    if value_var in df.columns:
        df["value"] = pd.to_numeric(df[value_var], errors="coerce")
    else:
        df["value"] = pd.NA

    path_out, sha = write_vintage(
        publisher="us_census",
        series_id=series_id,
        frame=df,
        fetch_utc=fetch_ts,
    )

    years_known = df["year"].dropna() if "year" in df.columns else pd.Series([], dtype="Int64")
    start_date = str(int(years_known.min())) if len(years_known) else (
        str(spec["year"]) if spec["year"] else None
    )
    end_date = str(int(years_known.max())) if len(years_known) else (
        str(spec["year"]) if spec["year"] else None
    )

    return FetchResult(
        publisher="us_census",
        series_id=series_id,
        source_url=f"{url}?{requests.compat.urlencode({k: v for k, v in params.items() if k != 'key'})}",
        methodology_url=METHODOLOGY,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(df),
        frequency=spec["frequency"],
        units=spec["units"],
        currency=None,
        start_date=start_date,
        end_date=end_date,
        sha256=sha,
        parquet_path=path_out,
        extra={
            "dataset": spec["dataset"],
            "year": spec["year"],
            "get_vars": spec["get"],
            "geo": spec.get("geo"),
            "extra_params": spec.get("extra_params"),
            "census_api_key_used": bool(api_key),
            "vintage_utc": vintage_utc.isoformat() if vintage_utc else None,
        },
    )
