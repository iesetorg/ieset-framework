#!/usr/bin/env python3
"""Build NYC rent-regulation stock proxy panel from pinned NYC Open Data views."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location("ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load data/fetchers/_base.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FETCHER_BASE = load_fetcher_base()
FetchResult = _FETCHER_BASE.FetchResult
utc_now = _FETCHER_BASE.utc_now
utc_stamp = _FETCHER_BASE.utc_stamp

SOCRATA_DOMAIN = "https://data.cityofnewyork.us"
SOURCE_URL = "https://opendata.cityofnewyork.us/"
METHODOLOGY_URL = "https://opendata.cityofnewyork.us/"
LICENSE = "NYC Open Data terms; verify per dataset metadata"
NYC_IESET_CITY_ID = "ghsl_ucdb_r2024a:8099"

DATASETS = {
    "dof_property_exemption_detail": {
        "id": "muvi-b6kx",
        "name": "Property Exemption Detail",
        "source_url": f"{SOCRATA_DOMAIN}/City-Government/Property-Exemption-Detail/muvi-b6kx",
        "publisher": "NYC Department of Finance",
    },
    "dof_exemption_classification_codes": {
        "id": "myn9-hwsy",
        "name": "Exemption Classification Codes",
        "source_url": f"{SOCRATA_DOMAIN}/City-Government/Exemption-Classification-Codes/myn9-hwsy",
        "publisher": "NYC Department of Finance",
    },
    "dof_property_abatement_detail": {
        "id": "rgyu-ii48",
        "name": "DOF Property Abatement Detail",
        "source_url": f"{SOCRATA_DOMAIN}/City-Government/DOF-Property-Abatement-Detail/rgyu-ii48",
        "publisher": "NYC Department of Finance",
    },
    "dof_j51_historical": {
        "id": "y7az-s7wc",
        "name": "J-51 Exemption and Abatement (Historical)",
        "source_url": f"{SOCRATA_DOMAIN}/City-Government/J-51-Exemption-and-Abatement-Historical/y7az-s7wc",
        "publisher": "NYC Department of Finance",
    },
    "hpd_421a16_completion_letters": {
        "id": "pq4c-wbq4",
        "name": "421-a(16) Affordable New York Housing Program Completion Extension - Letters of Intent",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/421-a-16-Affordable-New-York-Housing-Program-Comple/pq4c-wbq4",
        "publisher": "NYC Department of Housing Preservation and Development",
    },
    "hpd_485x_registrations": {
        "id": "rrtd-iyd7",
        "name": "485-x Affordable Neighborhoods for New Yorkers: Registrations of Prospective Applicants for Tax Benefits",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/485-x-Affordable-Neighborhoods-for-New-Yorkers-Regi/rrtd-iyd7",
        "publisher": "NYC Department of Housing Preservation and Development",
    },
    "dcp_pluto": {
        "id": "64uk-42ks",
        "name": "Primary Land Use Tax Lot Output (PLUTO)",
        "source_url": f"{SOCRATA_DOMAIN}/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO/64uk-42ks",
        "publisher": "NYC Department of City Planning",
    },
    "hpd_multiple_dwelling_registrations": {
        "id": "tesw-yqqr",
        "name": "Multiple Dwelling Registrations",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-Development/Multiple-Dwelling-Registrations/tesw-yqqr",
        "publisher": "NYC Department of Housing Preservation and Development",
    },
}

BOROUGH_ALIASES = {
    "1": "MANHATTAN",
    "2": "BRONX",
    "3": "BROOKLYN",
    "4": "QUEENS",
    "5": "STATEN ISLAND",
    "MN": "MANHATTAN",
    "BX": "BRONX",
    "BK": "BROOKLYN",
    "QN": "QUEENS",
    "SI": "STATEN ISLAND",
    "NEW YORK": "MANHATTAN",
    "RICHMOND": "STATEN ISLAND",
}

BENEFIT_FAMILIES = {
    "48076": "j51",
    "48806": "421a",
    "48826": "421g",
}


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def clean_text(value: object, default: str = "UNKNOWN") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def parse_int(value: object, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def parse_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value))
    except ValueError:
        return default


def normalize_borough(value: object) -> str:
    text = clean_text(value).upper().replace("_", " ")
    text = " ".join(text.split())
    return BOROUGH_ALIASES.get(text, text)


def fetch_query(dataset_id: str, query: str) -> list[dict[str, Any]]:
    url = f"{SOCRATA_DOMAIN}/resource/{dataset_id}.json?" + urllib.parse.urlencode({"$query": query})
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def fetch_metadata(dataset_id: str) -> dict[str, Any]:
    url = f"{SOCRATA_DOMAIN}/api/views/{dataset_id}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=60) as response:
        payload = json.load(response)
    return {
        "id": dataset_id,
        "name": payload.get("name"),
        "attribution": payload.get("attribution"),
        "rows_updated_at": payload.get("rowsUpdatedAt"),
        "columns": [column.get("fieldName") for column in payload.get("columns", []) if column.get("fieldName")],
    }


def nyc_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(NYC_IESET_CITY_ID)]
    if match.empty:
        match = spine[spine["city_name"].eq("New York City")]
    if match.empty:
        raise ValueError("could not find New York City in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        "country_name": row["country_name"],
    }


def code_lookup_query() -> str:
    return (
        "select exempt_code, sdea_code, description, legal_ref "
        "where sdea_code in('48076','48806','48826') "
        "order by sdea_code, exempt_code limit 5000"
    )


def property_exemption_query(start_year: int, end_year: int) -> str:
    return (
        "select year, boro, nys_exmp_code, exmp_code, count(*) as records, "
        "count(distinct parid) as parcels, sum(curexmptot) as exemption_amount "
        f"where year between '{start_year}' and '{end_year}' "
        "and nys_exmp_code in('48806','48076','48826') "
        "group by year, boro, nys_exmp_code, exmp_code "
        "order by year, boro, nys_exmp_code, exmp_code limit 50000"
    )


def property_abatement_query(start_year: int, end_year: int) -> str:
    return (
        "select taxyr, tccode, tcsubcode, count(*) as records, count(distinct parid) as parcels, "
        "sum(appliedabt) as abatement_amount "
        f"where taxyr between '{start_year}' and '{end_year}' and tccode like 'J51%' "
        "group by taxyr, tccode, tcsubcode order by taxyr, tccode, tcsubcode limit 50000"
    )


def j51_historical_query(start_year: int, end_year: int) -> str:
    return (
        "select tax_year, b, count(*) as records, sum(exempt_amt) as exemption_amount, "
        "sum(abatement) as abatement_amount "
        f"where tax_year between {start_year} and {end_year} "
        "group by tax_year, b order by tax_year, b limit 50000"
    )


def hpd_421a16_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(form_submission_date) as year, presumed_borough, reported_affordability_option, "
        "count(*) as records, sum(presumed_building_units) as units, "
        "sum(presumed_building_affordable) as restricted_units "
        f"where form_submission_date between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59' "
        "group by year, presumed_borough, reported_affordability_option "
        "order by year, presumed_borough, reported_affordability_option limit 50000"
    )


def hpd_485x_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(form_submission_date) as year, reported_property_borough, reported_affordability_option, "
        "count(*) as records, sum(presumed_building_units) as units, "
        "sum(presumed_restricted_units) as restricted_units "
        f"where form_submission_date between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59' "
        "group by year, reported_property_borough, reported_affordability_option "
        "order by year, reported_property_borough, reported_affordability_option limit 50000"
    )


def multiple_dwelling_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(lastregistrationdate) as year, boro, count(*) as records, "
        "count(distinct registrationid) as registrations, count(distinct bin) as buildings "
        f"where lastregistrationdate between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59' "
        "group by year, boro order by year, boro limit 50000"
    )


def pluto_query() -> str:
    return (
        "select borough, count(*) as tax_lots, sum(unitsres) as residential_units, "
        "sum(unitstotal) as total_units where borough is not null group by borough order by borough limit 50000"
    )


def base_row(
    city: dict[str, Any],
    dataset_key: str,
    year: object,
    borough: object,
    measure_name: str,
    value_count: object,
) -> dict[str, Any]:
    dataset = DATASETS[dataset_key]
    return {
        **city,
        "year": parse_int(year),
        "geography_level": "nyc_borough",
        "borough": normalize_borough(borough),
        "source_dataset_key": dataset_key,
        "source_dataset_id": dataset["id"],
        "source_dataset_name": dataset["name"],
        "publisher": dataset["publisher"],
        "measure_name": measure_name,
        "value_count": parse_int(value_count),
        "parcel_count": 0,
        "building_count": 0,
        "unit_count": 0,
        "restricted_unit_count": 0,
        "exemption_amount": 0.0,
        "abatement_amount": 0.0,
        "manual_review_required": False,
        "source_url": dataset["source_url"],
    }


def code_lookup(fetcher: Callable[[str, str], list[dict[str, Any]]]) -> dict[str, dict[str, str]]:
    items = fetcher(DATASETS["dof_exemption_classification_codes"]["id"], code_lookup_query())
    return {
        clean_text(item.get("exempt_code")): {
            "sdea_code": clean_text(item.get("sdea_code")),
            "description": clean_text(item.get("description")),
            "legal_ref": clean_text(item.get("legal_ref"), "NA"),
        }
        for item in items
    }


def property_exemption_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    lookup: dict[str, dict[str, str]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = property_exemption_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["dof_property_exemption_detail"]["id"], query):
        nys_code = clean_text(item.get("nys_exmp_code"))
        exmp_code = clean_text(item.get("exmp_code"))
        code_info = lookup.get(exmp_code, {})
        row = base_row(
            city,
            "dof_property_exemption_detail",
            item.get("year"),
            item.get("boro"),
            "dof_property_exemption_records",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": BENEFIT_FAMILIES.get(nys_code, "other"),
                "category_1": nys_code,
                "category_2": exmp_code,
                "category_3": code_info.get("description", "UNKNOWN"),
                "category_4": code_info.get("legal_ref", "NA"),
                "category_5": "current_property_exemption",
                "parcel_count": parse_int(item.get("parcels")),
                "exemption_amount": parse_float(item.get("exemption_amount")),
            }
        )
        rows.append(row)
    return rows, query


def property_abatement_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = property_abatement_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["dof_property_abatement_detail"]["id"], query):
        row = base_row(
            city,
            "dof_property_abatement_detail",
            item.get("taxyr"),
            "NYC",
            "dof_property_abatement_records",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": "j51",
                "category_1": clean_text(item.get("tccode")),
                "category_2": clean_text(item.get("tcsubcode")),
                "category_3": "J-51 property abatement",
                "category_4": "NA",
                "category_5": "current_property_abatement",
                "parcel_count": parse_int(item.get("parcels")),
                "abatement_amount": parse_float(item.get("abatement_amount")),
            }
        )
        rows.append(row)
    return rows, query


def j51_historical_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = j51_historical_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["dof_j51_historical"]["id"], query):
        row = base_row(
            city,
            "dof_j51_historical",
            item.get("tax_year"),
            item.get("b"),
            "historical_j51_records",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": "j51",
                "category_1": "48076",
                "category_2": "historical_j51",
                "category_3": "J-51 historical exemption and abatement",
                "category_4": "NA",
                "category_5": "historical_j51",
                "exemption_amount": parse_float(item.get("exemption_amount")),
                "abatement_amount": parse_float(item.get("abatement_amount")),
            }
        )
        rows.append(row)
    return rows, query


def hpd_421a16_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = hpd_421a16_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["hpd_421a16_completion_letters"]["id"], query):
        row = base_row(
            city,
            "hpd_421a16_completion_letters",
            item.get("year"),
            item.get("presumed_borough"),
            "hpd_421a16_letters_of_intent",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": "421a16",
                "category_1": clean_text(item.get("reported_affordability_option")),
                "category_2": "completion_extension_letter",
                "category_3": "Affordable New York / 421-a(16)",
                "category_4": "NA",
                "category_5": "tax_benefit_intent_proxy",
                "unit_count": parse_int(item.get("units")),
                "restricted_unit_count": parse_int(item.get("restricted_units")),
                "manual_review_required": True,
            }
        )
        rows.append(row)
    return rows, query


def hpd_485x_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = hpd_485x_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["hpd_485x_registrations"]["id"], query):
        row = base_row(
            city,
            "hpd_485x_registrations",
            item.get("year"),
            item.get("reported_property_borough"),
            "hpd_485x_prospective_registrations",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": "485x",
                "category_1": clean_text(item.get("reported_affordability_option")),
                "category_2": "prospective_tax_benefit_registration",
                "category_3": "485-x Affordable Neighborhoods for New Yorkers",
                "category_4": "NA",
                "category_5": "tax_benefit_intent_proxy",
                "unit_count": parse_int(item.get("units")),
                "restricted_unit_count": parse_int(item.get("restricted_units")),
                "manual_review_required": True,
            }
        )
        rows.append(row)
    return rows, query


def multiple_dwelling_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    start_year: int,
    end_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = multiple_dwelling_query(start_year, end_year)
    rows = []
    for item in fetcher(DATASETS["hpd_multiple_dwelling_registrations"]["id"], query):
        row = base_row(
            city,
            "hpd_multiple_dwelling_registrations",
            item.get("year"),
            item.get("boro"),
            "hpd_multiple_dwelling_registrations",
            item.get("records"),
        )
        row.update(
            {
                "benefit_family": "denominator",
                "category_1": "multiple_dwelling_registration",
                "category_2": "last_registration_year",
                "category_3": "NA",
                "category_4": "NA",
                "category_5": "building_stock_denominator",
                "parcel_count": parse_int(item.get("registrations")),
                "building_count": parse_int(item.get("buildings")),
            }
        )
        rows.append(row)
    return rows, query


def pluto_rows(
    city: dict[str, Any],
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    snapshot_year: int,
) -> tuple[list[dict[str, Any]], str]:
    query = pluto_query()
    rows = []
    for item in fetcher(DATASETS["dcp_pluto"]["id"], query):
        row = base_row(
            city,
            "dcp_pluto",
            snapshot_year,
            item.get("borough"),
            "pluto_tax_lot_denominators",
            item.get("tax_lots"),
        )
        row.update(
            {
                "benefit_family": "denominator",
                "category_1": "pluto_tax_lots",
                "category_2": "current_snapshot",
                "category_3": "NA",
                "category_4": "NA",
                "category_5": "housing_stock_denominator",
                "parcel_count": parse_int(item.get("tax_lots")),
                "unit_count": parse_int(item.get("total_units")),
                "restricted_unit_count": parse_int(item.get("residential_units")),
            }
        )
        rows.append(row)
    return rows, query


def build_panel(
    *,
    city_spine_path: Path,
    start_year: int,
    end_year: int,
    fetcher: Callable[[str, str], list[dict[str, Any]]] = fetch_query,
    metadata_fetcher: Callable[[str], dict[str, Any]] = fetch_metadata,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    city = nyc_city_record(city_spine_path)
    all_rows: list[dict[str, Any]] = []
    query_log: dict[str, list[str]] = {}

    lookup = code_lookup(fetcher)
    query_log["dof_exemption_classification_codes"] = [code_lookup_query()]

    for key, fn in [
        ("dof_property_exemption_detail", lambda: property_exemption_rows(city, fetcher, lookup, start_year, end_year)),
        ("dof_property_abatement_detail", lambda: property_abatement_rows(city, fetcher, start_year, end_year)),
        ("dof_j51_historical", lambda: j51_historical_rows(city, fetcher, start_year, end_year)),
        ("hpd_421a16_completion_letters", lambda: hpd_421a16_rows(city, fetcher, start_year, end_year)),
        ("hpd_485x_registrations", lambda: hpd_485x_rows(city, fetcher, start_year, end_year)),
        ("hpd_multiple_dwelling_registrations", lambda: multiple_dwelling_rows(city, fetcher, start_year, end_year)),
        ("dcp_pluto", lambda: pluto_rows(city, fetcher, end_year)),
    ]:
        rows, query = fn()
        all_rows.extend(rows)
        query_log[key] = [query]
        time.sleep(0.05)

    if not all_rows:
        raise ValueError("NYC rent-regulation proxy queries returned no aggregate rows")

    panel = pd.DataFrame(all_rows)
    columns = [
        "ieset_city_id",
        "city_name",
        "ghsl_city_rank_2025",
        "country_name",
        "year",
        "geography_level",
        "borough",
        "source_dataset_key",
        "source_dataset_id",
        "source_dataset_name",
        "publisher",
        "measure_name",
        "benefit_family",
        "category_1",
        "category_2",
        "category_3",
        "category_4",
        "category_5",
        "value_count",
        "parcel_count",
        "building_count",
        "unit_count",
        "restricted_unit_count",
        "exemption_amount",
        "abatement_amount",
        "manual_review_required",
        "source_url",
    ]
    panel = panel[columns].sort_values(
        ["source_dataset_key", "year", "borough", "benefit_family", "category_1", "category_2"]
    ).reset_index(drop=True)

    metadata = {key: metadata_fetcher(spec["id"]) for key, spec in DATASETS.items()}
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "borough_count": int(panel["borough"].nunique()),
        "benefit_families": sorted(str(value) for value in panel["benefit_family"].dropna().unique()),
        "datasets": {
            key: {
                "rows": int((panel["source_dataset_key"] == key).sum()),
                "value_count_sum": int(panel.loc[panel["source_dataset_key"] == key, "value_count"].sum()),
                "unit_count_sum": int(panel.loc[panel["source_dataset_key"] == key, "unit_count"].sum()),
                "restricted_unit_count_sum": int(
                    panel.loc[panel["source_dataset_key"] == key, "restricted_unit_count"].sum()
                ),
            }
            for key in DATASETS
            if key != "dof_exemption_classification_codes"
        },
        "query_count": sum(len(items) for items in query_log.values()),
        "metadata": metadata,
        "queries": query_log,
        "caveat": (
            "This is a public proxy panel for rent-regulation stock and tax-benefit exposure. "
            "It is not an apartment-level DHCR/HCR rent-registration file."
        ),
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_nyc_rent_regulation_tax_benefits.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "nyc_rent_regulation_tax_benefit_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="nyc_open_data",
        series_id="nyc_rent_regulation_tax_benefit_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual and current snapshot",
        units="aggregate counts, units, exemption dollars, and abatement dollars",
        currency="USD",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Server-side Socrata aggregates for public NYC rent-regulation stock proxies: "
                "421-a/421-g/J-51 exemptions, J-51 abatements, HPD 421-a(16)/485-x intent records, "
                "multiple-dwelling registrations, and PLUTO denominators. All rows attach to GHSL "
                "New York City while preserving borough detail."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/nyc_rent_regulation_tax_benefit_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--start-year", type=int, default=2007)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    panel, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        start_year=args.start_year,
        end_year=args.end_year,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    dataset_summary = ", ".join(f"{key}={value['rows']}" for key, value in stats["datasets"].items())
    print(
        "OK nyc_open_data:nyc_rent_regulation_tax_benefit_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} {dataset_summary}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
