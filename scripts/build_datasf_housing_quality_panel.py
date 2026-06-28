#!/usr/bin/env python3
"""Build a San Francisco housing/rent-control panel from pinned DataSF views."""
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

SOCRATA_DOMAIN = "https://data.sfgov.org"
SOURCE_URL = "https://datasf.org/opendata/"
METHODOLOGY_URL = "https://datasf.org/opendata/"
LICENSE = "DataSF terms; verify per dataset metadata"
SF_IESET_CITY_ID = "ghsl_ucdb_r2024a:1461"

DATASETS = {
    "building_permit": {
        "id": "i98e-djp9",
        "name": "Building Permits",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Building-Permits/i98e-djp9",
        "publisher": "City and County of San Francisco",
        "measure_name": "sf_building_permits_issued",
    },
    "dbi_complaint": {
        "id": "gm2e-bten",
        "name": "Department of Building Inspection Complaints (All Divisions)",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Department-of-Building-Inspection-Complaints-All-Div/gm2e-bten",
        "publisher": "San Francisco Department of Building Inspection",
        "measure_name": "sf_dbi_complaints",
    },
    "dbi_notice_of_violation": {
        "id": "nbtm-fbw5",
        "name": "Notices of Violation issued by the Department of Building Inspection",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Notices-of-Violation-issued-by-the-Department-of-B/nbtm-fbw5",
        "publisher": "San Francisco Department of Building Inspection",
        "measure_name": "sf_dbi_notices_of_violation",
    },
    "rent_board_inventory": {
        "id": "gdc7-dmcn",
        "name": "Rent Board Housing Inventory",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Rent-Board-Housing-Inventory/gdc7-dmcn",
        "publisher": "San Francisco Rent Board",
        "measure_name": "sf_rent_board_inventory_records",
    },
    "rent_board_petition": {
        "id": "6swy-cmkq",
        "name": "Petitions to the Rent Board",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Petitions-to-the-Rent-Board/6swy-cmkq",
        "publisher": "San Francisco Rent Board",
        "measure_name": "sf_rent_board_petitions",
    },
    "eviction_notice": {
        "id": "5cei-gny5",
        "name": "Eviction Notices",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Eviction-Notices/5cei-gny5",
        "publisher": "San Francisco Rent Board",
        "measure_name": "sf_eviction_notices",
    },
    "buyout_agreement": {
        "id": "wmam-7g8d",
        "name": "Buyout Agreements",
        "source_url": f"{SOCRATA_DOMAIN}/Housing-and-Buildings/Buyout-Agreements/wmam-7g8d",
        "publisher": "San Francisco Rent Board",
        "measure_name": "sf_buyout_agreements",
    },
}

EVICTION_REASON_FLAGS = [
    "non_payment",
    "breach",
    "owner_move_in",
    "demolition",
    "capital_improvement",
    "substantial_rehab",
    "ellis_act_withdrawal",
    "condo_conversion",
    "development",
]


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


def normalize_neighborhood(value: object) -> str:
    text = clean_text(value).replace("_", " ")
    return " ".join(text.split())


def fetch_query(dataset_id: str, query: str) -> list[dict[str, Any]]:
    url = f"{SOCRATA_DOMAIN}/resource/{dataset_id}.json?" + urllib.parse.urlencode({"$query": query})
    req = urllib.request.Request(url, headers={"User-Agent": "IESET city-level data builder"})
    with urllib.request.urlopen(req, timeout=120) as response:
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


def sf_city_record(city_spine_path: Path) -> dict[str, Any]:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = pd.read_csv(city_spine_path)
    match = spine[spine["ieset_city_id"].eq(SF_IESET_CITY_ID)]
    if match.empty:
        match = spine[spine["city_name"].eq("San Francisco")]
    if match.empty:
        raise ValueError("could not find San Francisco in city spine")
    row = match.iloc[0].to_dict()
    return {
        "ieset_city_id": row["ieset_city_id"],
        "city_name": row["city_name"],
        "ghsl_city_rank_2025": int(row["city_rank_2025"]),
        "country_name": row["country_name"],
    }


def date_between(field: str, start_year: int, end_year: int) -> str:
    return f"{field} between '{start_year}-01-01T00:00:00' and '{end_year}-12-31T23:59:59'"


def base_row(
    city: dict[str, Any],
    dataset_key: str,
    year: object,
    neighborhood: object,
    supervisor_district: object,
    value: object,
) -> dict[str, Any]:
    dataset = DATASETS[dataset_key]
    return {
        **city,
        "year": parse_int(year),
        "geography_level": "sf_analysis_neighborhood",
        "neighborhood": normalize_neighborhood(neighborhood),
        "supervisor_district": clean_text(supervisor_district),
        "source_dataset_key": dataset_key,
        "source_dataset_id": dataset["id"],
        "source_dataset_name": dataset["name"],
        "source_url": dataset["source_url"],
        "publisher": dataset["publisher"],
        "measure_name": dataset["measure_name"],
        "value": parse_int(value),
        "manual_review_required": False,
    }


def rows_from_items(
    city: dict[str, Any],
    dataset_key: str,
    items: list[dict[str, Any]],
    *,
    neighborhood_field: str,
    supervisor_field: str,
    category_fields: list[str],
    category_defaults: list[str] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    category_defaults = category_defaults or []
    for item in items:
        row = base_row(
            city,
            dataset_key,
            item.get("year"),
            item.get(neighborhood_field),
            item.get(supervisor_field),
            item.get("value"),
        )
        for index in range(5):
            default = category_defaults[index] if index < len(category_defaults) else "NA"
            field = category_fields[index] if index < len(category_fields) else None
            row[f"category_{index + 1}"] = clean_text(item.get(field), default) if field else default
        rows.append(row)
    return rows


def building_permit_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(issued_date) as year, neighborhoods_analysis_boundaries, supervisor_district, "
        "permit_type_definition, adu, count(*) as value "
        f"where {date_between('issued_date', start_year, end_year)} "
        "group by year, neighborhoods_analysis_boundaries, supervisor_district, permit_type_definition, adu "
        "order by year, neighborhoods_analysis_boundaries, supervisor_district, permit_type_definition, adu "
        "limit 50000"
    )


def dbi_complaint_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(date_filed) as year, analysis_neighborhood, supervisor_district, "
        "receiving_division, status, count(*) as value "
        f"where {date_between('date_filed', start_year, end_year)} "
        "group by year, analysis_neighborhood, supervisor_district, receiving_division, status "
        "order by year, analysis_neighborhood, supervisor_district, receiving_division, status "
        "limit 50000"
    )


def dbi_notice_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(date_filed) as year, neighborhoods_analysis_boundaries, supervisor_district, "
        "nov_category_description, work_without_permit, unsafe_building, count(*) as value "
        f"where {date_between('date_filed', start_year, end_year)} "
        "group by year, neighborhoods_analysis_boundaries, supervisor_district, "
        "nov_category_description, work_without_permit, unsafe_building "
        "order by year, neighborhoods_analysis_boundaries, supervisor_district, "
        "nov_category_description, work_without_permit, unsafe_building "
        "limit 50000"
    )


def rent_board_inventory_query(start_year: int, end_year: int) -> str:
    return (
        "select submission_year as year, analysis_neighborhood, supervisor_district, "
        "case_type_name, occupancy_type, bedroom_count, count(*) as value "
        f"where submission_year between '{start_year}' and '{end_year}' "
        "group by year, analysis_neighborhood, supervisor_district, case_type_name, occupancy_type, bedroom_count "
        "order by year, analysis_neighborhood, supervisor_district, case_type_name, occupancy_type, bedroom_count "
        "limit 50000"
    )


def rent_board_petition_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(date_filed) as year, neighborhoods_analysis_boundaries, supervisor_district, "
        "filing_party, priority, count(*) as value "
        f"where {date_between('date_filed', start_year, end_year)} "
        "group by year, neighborhoods_analysis_boundaries, supervisor_district, filing_party, priority "
        "order by year, neighborhoods_analysis_boundaries, supervisor_district, filing_party, priority "
        "limit 50000"
    )


def eviction_notice_query(start_year: int, end_year: int, reason_flag: str | None = None) -> str:
    reason_filter = f" and {reason_flag} = true" if reason_flag else ""
    return (
        "select date_extract_y(file_date) as year, neighborhood, supervisor_district, count(*) as value "
        f"where {date_between('file_date', start_year, end_year)}{reason_filter} "
        "group by year, neighborhood, supervisor_district "
        "order by year, neighborhood, supervisor_district "
        "limit 50000"
    )


def buyout_agreement_query(start_year: int, end_year: int) -> str:
    return (
        "select date_extract_y(buyout_agreement_date) as year, analysis_neighborhood, supervisor_district, "
        "count(*) as value "
        f"where {date_between('buyout_agreement_date', start_year, end_year)} "
        "group by year, analysis_neighborhood, supervisor_district "
        "order by year, analysis_neighborhood, supervisor_district "
        "limit 50000"
    )


def query_rows(
    city: dict[str, Any],
    dataset_key: str,
    query: str,
    fetcher: Callable[[str, str], list[dict[str, Any]]],
    *,
    neighborhood_field: str,
    supervisor_field: str,
    category_fields: list[str],
    category_defaults: list[str] | None = None,
) -> list[dict[str, Any]]:
    dataset_id = DATASETS[dataset_key]["id"]
    items = fetcher(dataset_id, query)
    return rows_from_items(
        city,
        dataset_key,
        items,
        neighborhood_field=neighborhood_field,
        supervisor_field=supervisor_field,
        category_fields=category_fields,
        category_defaults=category_defaults,
    )


def build_panel(
    *,
    city_spine_path: Path,
    start_year: int,
    end_year: int,
    fetcher: Callable[[str, str], list[dict[str, Any]]] = fetch_query,
    metadata_fetcher: Callable[[str], dict[str, Any]] = fetch_metadata,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    city = sf_city_record(city_spine_path)
    all_rows: list[dict[str, Any]] = []
    query_log: dict[str, list[str]] = {}

    query = building_permit_query(start_year, end_year)
    query_log["building_permit"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "building_permit",
            query,
            fetcher,
            neighborhood_field="neighborhoods_analysis_boundaries",
            supervisor_field="supervisor_district",
            category_fields=["permit_type_definition", "adu"],
            category_defaults=["UNKNOWN", "UNSPECIFIED"],
        )
    )
    time.sleep(0.05)

    query = dbi_complaint_query(start_year, end_year)
    query_log["dbi_complaint"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "dbi_complaint",
            query,
            fetcher,
            neighborhood_field="analysis_neighborhood",
            supervisor_field="supervisor_district",
            category_fields=["receiving_division", "status"],
        )
    )
    time.sleep(0.05)

    query = dbi_notice_query(start_year, end_year)
    query_log["dbi_notice_of_violation"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "dbi_notice_of_violation",
            query,
            fetcher,
            neighborhood_field="neighborhoods_analysis_boundaries",
            supervisor_field="supervisor_district",
            category_fields=["nov_category_description", "work_without_permit", "unsafe_building"],
        )
    )
    time.sleep(0.05)

    query = rent_board_inventory_query(start_year, end_year)
    query_log["rent_board_inventory"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "rent_board_inventory",
            query,
            fetcher,
            neighborhood_field="analysis_neighborhood",
            supervisor_field="supervisor_district",
            category_fields=["case_type_name", "occupancy_type", "bedroom_count"],
        )
    )
    time.sleep(0.05)

    query = rent_board_petition_query(start_year, end_year)
    query_log["rent_board_petition"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "rent_board_petition",
            query,
            fetcher,
            neighborhood_field="neighborhoods_analysis_boundaries",
            supervisor_field="supervisor_district",
            category_fields=["filing_party", "priority"],
        )
    )
    time.sleep(0.05)

    query = eviction_notice_query(start_year, end_year)
    query_log["eviction_notice"] = [query]
    rows = query_rows(
        city,
        "eviction_notice",
        query,
        fetcher,
        neighborhood_field="neighborhood",
        supervisor_field="supervisor_district",
        category_fields=[],
        category_defaults=["all_eviction_notices"],
    )
    all_rows.extend(rows)
    time.sleep(0.05)

    for reason_flag in EVICTION_REASON_FLAGS:
        query = eviction_notice_query(start_year, end_year, reason_flag)
        query_log["eviction_notice"].append(query)
        rows = query_rows(
            city,
            "eviction_notice",
            query,
            fetcher,
            neighborhood_field="neighborhood",
            supervisor_field="supervisor_district",
            category_fields=[],
            category_defaults=[reason_flag],
        )
        all_rows.extend(rows)
        time.sleep(0.05)

    query = buyout_agreement_query(start_year, end_year)
    query_log["buyout_agreement"] = [query]
    all_rows.extend(
        query_rows(
            city,
            "buyout_agreement",
            query,
            fetcher,
            neighborhood_field="analysis_neighborhood",
            supervisor_field="supervisor_district",
            category_fields=[],
            category_defaults=["buyout_agreements"],
        )
    )

    if not all_rows:
        raise ValueError("DataSF queries returned no aggregate rows")

    panel = pd.DataFrame(all_rows)
    columns = [
        "ieset_city_id",
        "city_name",
        "ghsl_city_rank_2025",
        "country_name",
        "year",
        "geography_level",
        "neighborhood",
        "supervisor_district",
        "source_dataset_key",
        "source_dataset_id",
        "source_dataset_name",
        "publisher",
        "measure_name",
        "category_1",
        "category_2",
        "category_3",
        "category_4",
        "category_5",
        "value",
        "manual_review_required",
        "source_url",
    ]
    panel = panel[columns].sort_values(
        [
            "source_dataset_key",
            "year",
            "neighborhood",
            "supervisor_district",
            "category_1",
            "category_2",
            "category_3",
        ]
    ).reset_index(drop=True)

    metadata = {key: metadata_fetcher(spec["id"]) for key, spec in DATASETS.items()}
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "neighborhood_count": int(panel["neighborhood"].nunique()),
        "datasets": {
            key: {
                "rows": int((panel["source_dataset_key"] == key).sum()),
                "value_sum": int(panel.loc[panel["source_dataset_key"] == key, "value"].sum()),
            }
            for key in DATASETS
        },
        "query_count": sum(len(items) for items in query_log.values()),
        "metadata": metadata,
        "queries": query_log,
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_datasf_housing_quality_supply.yaml"
    payload = {"run_utc": run_stamp, "pipeline": "datasf_housing_quality_supply_panel", "entries": [manifest_entry(result)]}
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def emit(panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="datasf",
        series_id="us_sf_rent_control_quality_leakage_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="annual aggregate counts",
        currency=None,
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "construction": (
                "Server-side Socrata aggregates by year, analysis neighborhood, supervisor district, "
                "and dataset-specific categories. All rows attach to GHSL San Francisco while preserving "
                "local neighborhood detail."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.csv")
    parser.add_argument("--output", default="data/derived/us_sf_rent_control_quality_leakage_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--start-year", type=int, default=1997)
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
        "OK datasf:us_sf_rent_control_quality_leakage_panel "
        f"rows={result.rows} period={result.start_date}->{result.end_date} {dataset_summary}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
